# -*- coding: utf-8 -*-

import re
import itertools

from django.shortcuts import render_to_response, get_list_or_404, \
    get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
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
from votes.models import Party, Session, PlenarySession, Term, DistrictAssociation
from votes.views import DISTRICT_KEY
from httpstatus import Http400, Http403
from httpstatus.decorators import postonly
from kamu.cms.models import Item
from operator import attrgetter
from sorl.thumbnail.main import DjangoThumbnail
from votes.views import find_term, find_district

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


def show_question(request, source, question):
    src = get_object_or_404(QuestionSource, url_name=source)
    try:
        question = int(question)
    except ValueError:
        raise Http404()
    question = get_object_or_404(Question, source=src, order=question)
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

    args = dict(question=question, relevant_sessions=relevant_sessions)
    args['active_page'] = 'opinions'
    args['opinions_page'] = 'show_questions'

    if request.session:
        request.session[LAST_QUESTION_KEY] = question

    context_instance = RequestContext(request)
    response = render_to_response('opinions/show_question.html', args,
                                  context_instance=context_instance)

    return response

def show_question_session(request, source, question_no, plsess, sess_no, party=None):
    # TODO: Mapping url to the model objects could be a bit more concise
    src = get_object_or_404(QuestionSource, url_name=source)
    try:
        question_no = int(question_no)
    except ValueError:
        raise Http404()
    question = get_object_or_404(Question, source=src, order=question_no)

    try:
        number = int(sess_no)
    except ValueError:
        raise Http404
    psess = get_object_or_404(PlenarySession, url_name=plsess)
    session = get_object_or_404(Session, plenary_session=psess, number=sess_no)


    filter_args = dict(for_user=request.user,
                       for_question=question,
                       for_session=session)

    parties = VoteOptionCongruence.objects.get_party_congruences(
                    **filter_args)

    members = VoteOptionCongruence.objects.get_member_congruences(
                    **filter_args)
    # A hack to have a unified duck-typing API with "non-average" congruences
    # TODO: Get rid of this in non-demo code
    members = list(members)
    for m in members:
        tn = DjangoThumbnail(m.photo, (30, 40))
        m.thumbnail = tn
        m.congruence = m.congruence_avg
    
    party = request.GET.get('party', None)
    # This should be done in the query
    if party is not None:
        members = [m for m in members if m.party_id == party]
        party = get_object_or_404(Party, pk=party)
    
    parties = list(parties)
    for p in parties:
        tn = DjangoThumbnail(p.logo, (30, 40))
        p.thumbnail = tn
        p.congruence = p.congruence_avg
    
    args = dict(parties=parties,
                members=members,
                question=question,
                session=session,
                party=party,
                opinions_page='show_question_session')

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
    args['switch_term'] = True
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
