# -*- coding: utf-8 -*-

import re
import itertools
import simplejson
import math

from django.shortcuts import render_to_response, get_list_or_404, \
    get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from kamu.user_voting import models as user_voting
from opinions.models import *
from opinions.forms import VoteOptionCongruenceForm
from user_voting.models import Vote as UserVote
from votes.models import Party, Session, PlenarySession, Term, \
    TermMember, DistrictAssociation, Member
from votes.views import DISTRICT_KEY
from httpstatus import Http400, Http403
from httpstatus.decorators import postonly
from kamu.cms.models import Item
from operator import attrgetter
from sorl.thumbnail.main import DjangoThumbnail
from votes.views import find_term, find_district
from django.contrib.csrf.middleware import csrf_exempt

MATCH_PERM = 'opinions.change_questionsessionrelevance'
LAST_QUESTION_KEY = 'opinions:last_question'

def _handle_congruence_form(request, form, option, session):
    if not request.user.is_authenticated():
        raise Http403

    value = form.cleaned_data['congruence']
    if value is None or value == '':
        return

    value = int(value)

    value = value / 3.0
    item = VoteOptionCongruence(option=option, session=session,
                                congruence=value, vote='Y', user=request.user)
    item.save(update_if_exists=True)
    item = VoteOptionCongruence(option=option, session=session,
                                congruence=-value, vote='N', user=request.user)
    item.save(update_if_exists=True)

def find_question(source, question_nr):
    src = get_object_or_404(QuestionSource, url_name=source)
    try:
        question_nr = int(question_nr)
    except ValueError:
        raise Http404()
    return get_object_or_404(Question, source=src, order=question_nr)

def get_member_answer(request, source, question, member):
    question = find_question(source, question)
    mem = get_object_or_404(Member, url_name=member)
    ans = Answer.objects.filter(member=mem, question=question)
    if not ans:
        raise Http404()
    ans = ans[0]
    d = {}
    if ans.explanation:
        d['explanation'] = ans.explanation
    if ans.option:
        d['option'] = ans.option.order
        d['option_text'] = ans.option.name
    json = simplejson.dumps(d)
    return HttpResponse(json, mimetype='application/javascript')

def show_question(request, source, question):
    question = find_question(source, question)
    relevant_sessions = \
        QuestionSessionRelevance.get_relevant_sessions(question)
    relevant_sessions = relevant_sessions[:3]
    options = list(question.option_set.all())

    has_input = False
    cong_user = request.user
    if not cong_user.is_authenticated():
        cong_user = VoteOptionCongruence.objects.get_congruence_user(cong_user)

    for session in relevant_sessions:
        session.question_relevance = int(round(session.question_relevance * 100))
        option_congruences = []
        for option in options:
            user_congruence = None
            if cong_user is not None:
                user_congruence = \
                    list(VoteOptionCongruence.objects.filter(option=option,
                         session=session, vote='Y', user=cong_user))
                assert len(user_congruence) <= 1
                if len(user_congruence) > 0:
                    user_congruence = int(round(user_congruence[0].congruence * 3))
                else:
                    user_congruence = None

            data = None
            if request.method == 'POST':
                data = request.POST

            name = '%i_%i' % (session.id, option.id)
            input_form = VoteOptionCongruenceForm(data=data, prefix=name,
                    initial={'congruence': user_congruence})
            if not request.user.is_authenticated():
                input_form.fields['congruence'].widget.attrs['disabled'] = 'disabled'

            if input_form.is_valid():
                has_input = True
                _handle_congruence_form(request, input_form, option, session)

            congruence = VoteOptionCongruence.objects.get_congruence(option, session)
            if congruence is None:
                congruence = 0
            congruence_scale = int(round((congruence + 1) / 2.0 * 100))

            option_congruences.append(dict(input_form=input_form,
                                      option=option,
                                      congruence_scale=congruence_scale,
                                      user_congruence=user_congruence))
        session.option_congruences = option_congruences

    if has_input:
        return HttpResponseRedirect(
                reverse('opinions.views.show_question',
                        kwargs=dict(source=source, question=question.order)))

    answers = Answer.objects.filter(question=question)

    args = dict(question=question, answers=answers,
            relevant_sessions=relevant_sessions)
    args['active_page'] = 'opinions'
    args['opinions_page'] = 'show_questions'

    if request.session:
        request.session[LAST_QUESTION_KEY] = question

    context_instance = RequestContext(request)
    response = render_to_response('opinions/show_question.html', args,
                                  context_instance=context_instance)

    return response

def get_color(val):
    if val > 0:
        c = math.sqrt(1.0 - val) * 200
        rgb = (c, 200, c)
    else:
        c = math.sqrt(1.0 + val) * 200
        rgb = (200, c, c)
    return "#%02x%02x%02x" % rgb

def compare_question_and_session(request, question, vote_map, term, vote_by_mp=None):
    mp_list = TermMember.objects.filter(term=term).values_list('member', flat=True)

    options = Option.objects.filter(question=question)
    opt_dict = {}
    opt_json = {}
    for opt in options:
        val = vote_map.get(opt.order, 0)
        color = None
        if val > 0:
            vote_class = 'yes_vote'
            color = get_color(val)
        elif val < 0:
            vote_class = 'no_vote'
            color = get_color(val)
        else:
            vote_class = 'empty_vote'
        opt.vote_class = vote_class
        d = {'congruence': val}
        if color:
            opt.color_str = color
            d['color'] = opt.color_str

        opt_dict[opt.id] = opt
        opt_json[opt.order] = d

    parties = Party.objects.all().order_by('name')
    party_by_id = {}
    for party in parties:
        party.thumbnail = DjangoThumbnail(party.logo, (30, 30))
        party_by_id[party.pk] = party

    q = Answer.objects.filter(question=question, member__in=mp_list)
    answers = list(q.values_list('member', 'option__order'))
    ans_by_mp = dict((ans[0], ans[1]) for ans in answers)
    members = Member.objects.filter(id__in=mp_list)

    mp_json = []
    for mp in members:
        tn = DjangoThumbnail(mp.photo, (30, 40))
        party = party_by_id[mp.party_id]
        d = {'name': mp.name}
        if mp.id in ans_by_mp:
            d['answer'] = ans_by_mp[mp.id]
        d['id'] = mp.url_name
        d['url'] = mp.get_absolute_url()
        d['party'] = party.name
        d['party_logo'] = party.thumbnail.absolute_url
        d['portrait'] = tn.absolute_url
        if vote_by_mp and mp.pk in vote_by_mp:
            d['vote'] = vote_by_mp[mp.pk]
        mp_json.append(d)

    party_json = {}
    for party in parties:
        d = {'name': party.full_name}
        d['logo'] = party.thumbnail.absolute_url
        party_json[party.name] = d

    args = dict(question=question, options=options,
                parties=parties)
    args['mp_json'] = simplejson.dumps(mp_json)
    args['opt_json'] = simplejson.dumps(opt_json)
    args['party_json'] = simplejson.dumps(party_json)
    return args

def show_hypothetical_vote(request, source, question,
                           vote_name, vote_map, term):
    term = get_object_or_404(Term, name=term)
    src = get_object_or_404(QuestionSource, url_name=source)
    try:
        question_no = int(question)
    except ValueError:
        raise Http404()
    question = get_object_or_404(Question, source=src, order=question_no)

    args = compare_question_and_session(request, question,
                                        vote_map, term)
    args['vote_name'] = vote_name
    args['active_page'] = 'opinions'
    args['opinions_page'] = 'show_hypothetical_vote'
    response = render_to_response('opinions/show_hypothetical_vote.html', args,
                                  context_instance=RequestContext(request))
    return response

def show_question_session(request, source, question, plsess, session, vote_name=None):
    # TODO: Mapping url to the model objects could be a bit more concise
    src = get_object_or_404(QuestionSource, url_name=source)
    try:
        question = int(question)
    except ValueError:
        raise Http404()
    question = get_object_or_404(Question, source=src, order=question)

    try:
        number = int(session)
    except ValueError:
        raise Http404()
    psess = get_object_or_404(PlenarySession, url_name=plsess)
    session = get_object_or_404(Session, plenary_session=psess, number=number)

    term = session.plenary_session.term
    cong_user = VoteOptionCongruence.objects.get_congruence_user(request.user)
    vote_map = VoteOptionCongruence.objects.filter(user=cong_user,
                                                   session=session,
                                                   vote='Y',
                                                   option__in=question.option_set.all())
    vote_map = dict((c.option.order, c.congruence) for c in vote_map)

    votes = Vote.objects.filter(session=session)
    vote_by_mp = dict((vote.member_id, vote.vote) for vote in votes)
    for vote in votes:
        vote_by_mp[vote.member_id] = vote.vote

    args = compare_question_and_session(request, question, vote_map, term, vote_by_mp)

    vote_json = {}

    vote_json['Y'] = {'color': get_color(1), 'class_img': 'yes_vote'}
    vote_json['N'] = {'color': get_color(-1), 'class_img': 'no_vote'}
    vote_json['E'] = {'color': (200, 200, 200), 'class_img': 'empty_vote'}
    vote_json['A'] = {'color': (200, 200, 200), 'class_img': 'absent_vote'}

    args['vote_name'] = vote_name
    args['opinions_page'] = 'show_question_session'
    args['active_page'] = 'opinions'
    args['vote_json'] = simplejson.dumps(vote_json)
    session.info = session.info.replace('\n', '\n\n')
    args['session'] = session

    return render_to_response('opinions/show_question_session.html', args,
                              context_instance=RequestContext(request))

def list_questions(request):
    term = find_term(request)
    year = str(term.begin).split('-')[0]
    # FIXME: Show only questions from sources in chosen year

    questions = VoteOptionCongruence.objects.get_question_congruences(
                        allow_null_congruences=True, for_user=request.user)

    parties = Party.objects.all()

    args = dict(questions=questions, parties=parties)
    args['active_page'] = 'opinions'
    args['opinions_page'] = 'list_questions'
    args['switch_term'] = True
    return render_to_response('opinions/list_questions.html', args,
                              context_instance=RequestContext(request))

def clear_cache(sender, **kwargs):
    # FIXME: oh my
    k = cache.get('opinions_summary_keys')
    if not k:
        return
    cache.delete_many(k)
    cache.delete('opinions_summary_keys')
post_save.connect(clear_cache, sender=VoteOptionCongruence)
post_save.connect(clear_cache, sender=UserVote)

def save_cache(key, arg):
    cache.set(key, arg, 1200)
    k = cache.get('opinions_summary_keys')
    if not k:
        k = []
    k.append(key)
    cache.set('opinions_summary_keys', k, 1200)

def get_member_congs(member_list, user, question):
    member_congs = []
    for member in member_list:
        get_cong = VoteOptionCongruence.objects.get_member_congruence
        member.congruence = get_cong(member, for_user=user,
                                     for_question=question)
        if member.congruence is None:
            continue
        member_congs.append(member)

    member_congs.sort(key=attrgetter('name'))
    member_congs.sort(key=attrgetter('congruence'), reverse=True)

    return member_congs

def get_promise_statistics_summary(district, user, question=None):
    cache_key = "opinions_summary/%s/%s" % (user, question)
    if district:
        cache_key += "/%s" % (district)

    ret = cache.get(cache_key)
    if ret:
        return ret
    # workaround for un-pickleable django lazy objects
    if type(user) == SimpleLazyObject:
        user = user._wrapped

    get_party_cong = VoteOptionCongruence.objects.get_party_congruences
    parties = list(get_party_cong(for_user=user, for_question=question))
    # If no congruences found for parties, skip the other queries.
    if not parties:
        return {}

    if district:
        term = Term.objects.order_by('-begin')[0]
        members = Member.objects.in_district(district, term.begin, term.end)
    else:
        members = Member.objects.all()
        district = None

    member_congs = get_member_congs(members, user, question)
    for m in member_congs:
        tn = DjangoThumbnail(m.photo, (30, 40))
        m.thumbnail = tn

    ret = dict(parties=parties, members=member_congs, user=user,
                question=question, district=district)
    save_cache(cache_key, ret)

    return ret

def summary(request):
    term = find_term(request)
    district = find_district(request, term.begin, term.end)

    args = get_promise_statistics_summary(district, user=request.user)
    args['active_page'] = 'opinions'
    args['opinions_page'] = 'summary'
    args['content'] = Item.objects.retrieve_content('opinions_about')
    args['no_percentages'] = True
    args['switch_district'] = True
    return render_to_response('opinions/summary.html', args,
                            context_instance=RequestContext(request))

@postonly
def match_session(request):
    if not request.user.is_authenticated():
        raise Http403()

    s = request.POST.get('session', None)
    if not s or len(s) > 200:
        raise Http400()
    m = re.match(r'^(\d+/\d+/\d+)$', s)
    if not m:
        raise Http400()
    try:
        sess = Session.objects.by_name(s)
    except Session.DoesNotExist:
        raise Http404()

    s = request.POST.get('question', None)
    if not s or len(s) > 200:
        raise Http400()
    m = re.match(r'^\w+/\d+$', s)
    if not m:
        raise Http400()
    src_name, q_name = s.split('/')
    q_nr = int(q_name)
    try:
        src = QuestionSource.objects.get(url_name=src_name)
        question = Question.objects.get(source=src, order=q_nr)
    except QuestionSource.DoesNotExist, Question.DoesNotExist:
        raise Http404()

    if 'remove' in request.POST:
        delete = True
    else:
        delete = False
    try:
        rel = QuestionSessionRelevance.objects.get(question=question,
                session=sess, user=request.user)
    except QuestionSessionRelevance.DoesNotExist:
        if delete:
            raise Http404()
        rel = QuestionSessionRelevance(question=question, session=sess,
                                       user=request.user)
    if not delete:
        rel.relevance = 1.00
        rel.save()
        messages.add_message(request, messages.INFO, _('Session connected to question.'))
    else:
        rel.delete()
        messages.add_message(request, messages.INFO, _('Session removed from question.'))

    args = {'source': src.url_name, 'question': question.order}
    return HttpResponseRedirect(reverse('opinions.views.show_question', kwargs=args))

def weighted_congruence(l):
    return sum(l)/sum(abs(x) for x in l)

def show_party_congruences(request, party):
    for_party = get_object_or_404(Party, pk=party)
    # TODO: This is quite expensive because all questions/options/answers
    #       are fetched separatedly. There should be a way to get related
    #       objects with raw queries
    congruences = VoteOptionCongruence.objects.get_vote_congruences(
                    for_party=for_party, for_user=request.user)
    congruences = list(congruences)

    by_question = itertools.groupby(congruences, lambda c: c.option.question_id)
    questions = []
    for qid, congruences in by_question:
        q = Question.objects.get(pk=qid)
        congruences = list(congruences)
        total = float(len(congruences))
        q.congruence = weighted_congruence([c.congruence for c in congruences])

        option_cong = itertools.groupby(congruences, lambda c: c.option_id)
        option_cong = [(o, list(c)) for o, c in option_cong]
        option_cong = dict(option_cong)

        options = []
        for option in q.option_set.all():
            c = list(option_cong.get(option.id, []))
            option.congruences = list(c)
            option.share = int(round(len(option.congruences)/total*100))
            options.append(option)

        q.options = options

        by_session = sorted(congruences, key=lambda c: c.session_id)
        by_session = itertools.groupby(by_session, lambda c: c.session_id)
        sessions = []
        for sid, c in by_session:
            session = Session.objects.get(pk=sid)
            c = list(c)
            session.congruence = weighted_congruence([d.congruence for d in c])
            votes = [c.vote for c in c]
            total = float(len(votes))
            session.yay_share = int(round(votes.count('Y')/total*100))
            session.nay_share = int(round(votes.count('N')/total*100))
            sessions.append(session)

        q.sessions = sessions

        questions.append(q)

    args = dict(questions=questions, party=for_party)
    args['active_page'] = 'opinions'
    args['opinions_page'] = 'party'
    return render_to_response('opinions/show_party_congruences.html', args,
                              context_instance=RequestContext(request))

import cohesion

coalition_question_list = list(QuestionSource.objects.get(url_name='yle2011').\
                question_set.all().select_related('source__name'))
coalition_term = Term.objects.get(name='2011-2014')
stats_cache = cohesion.cached_all_cabinet_statistics(coalition_question_list, coalition_term)

@csrf_exempt
def update_coalition(request):
    try:
        post = request.POST
        if not post:
            raise Http400()
    except IOError:
        raise Http400()

    if not 'gov_parties[]' in post:
        request.session['coalition_parties'] = []
        return HttpResponse(mimetype='application/javascript')
    party_list = list(Party.objects.all())
    json = post.getlist('gov_parties[]')
    if len(json) > len(party_list):
        raise Http400()
    gov_list = []
    for gp in json:
        for p in party_list:
            if p.name == gp:
                gov_list.append(p)
                break
        else:
            raise Http400()

    request.session['coalition_parties'] = gov_list

    q_pk_list = None
    if 'questions[]' in post:
        q_list = post.getlist('questions[]')
        questions = []
        q_pk_list = []
        q_names = [str(q) for q in coalition_question_list]
        for q_name in q_list:
            if q_name not in q_names:
                raise Http404()
            q = coalition_question_list[q_names.index(q_name)]
            questions.append(q)
            q_pk_list.append(q.pk)

    cab_stats = stats_cache([p.name for p in gov_list], q_pk_list)
    chosen_cohesion = cab_stats.cohesion()

    cabinet_cohesions = stats_cache.majority_cohesions(q_pk_list)

    if not q_pk_list:
        q_pk_list = cab_stats.questions
        questions = Question.objects.filter(pk__in=cab_stats.questions)

    question_stats = []
    for q in questions:
        d = {'id': '%s/%d' % (q.source.url_name, q.order)}
        d['cohesion'] = round(cab_stats.cohesion(question=q.pk), 4)
        d['selected'] = q.pk in q_pk_list
        d['cabinet_answer'] = cab_stats.cabinet_answer(q.pk)
        question_stats.append(d)

    stats = {}
    for party in gov_list:
        stats[party.name] = round(cab_stats.cohesion(party=party.name), 4)

    d = {"party_stats": stats,
        "question_stats": question_stats,
        "selected_cohesion": chosen_cohesion,
        "cabinet_cohesions": cabinet_cohesions}
    json = simplejson.dumps(d)

    return HttpResponse(json, mimetype='application/javascript')

def display_coalition(request):
    party_list = list(Party.objects.all())
    party_json = []
    term = Term.objects.latest()

    gov_list = request.session.get('coalition_parties', None)
    if gov_list == None:
        # six-pack default
        DEFAULT_PARTIES = ('kok', 'sd', 'vas', 'kd', 'vihr', 'r')
        gov_list = []
        for pn in DEFAULT_PARTIES:
            for p in party_list:
                if p.name == pn:
                    gov_list.append(p)
                    break

    for party in party_list:
        tn = DjangoThumbnail(party.logo, (38, 38))
        d = {'id': party.name, 'name': party.full_name}
        d['logo'] = tn.absolute_url
        d['logo_dim'] = dict(x=tn.width(), y=tn.height())
        mp_list = Member.objects.active_in_term(term)
        seats = mp_list.filter(party=party).count()
        d['nr_seats'] = seats
        for gp in gov_list:
            if party.pk == gp.pk:
                d['gov'] = True
                break
        else:
            d['gov'] = False

        party_json.append(d)

    q_models = Question.objects.filter(pk__in=stats_cache.questions)
    q_models = q_models.select_related('source')

    question_json = []
    for idx, q in enumerate(q_models):
        name = '%s/%d' % (q.source.url_name, q.order)
        d = {'id': name, 'text': q.text}
        d['order'] = idx
        d['selected'] = True
        question_json.append(d)

    args = {'party_json': simplejson.dumps(party_json)}
    args['content'] = Item.objects.retrieve_content('coalition')
    args['question_json'] = simplejson.dumps(question_json)
    args['active_page'] = 'opinions'
    return render_to_response('opinions/coalition.html', args,
                              context_instance=RequestContext(request))
