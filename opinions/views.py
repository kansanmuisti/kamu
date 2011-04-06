# -*- coding: utf-8 -*-

import re

from django.shortcuts import render_to_response, get_list_or_404, \
    get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from opinions.models import *
from opinions.forms import VoteOptionCongruenceForm
from votes.models import Party, Session
from httpstatus import Http400, Http403
from httpstatus.decorators import postonly

MATCH_PERM = 'opinions.change_questionsessionrelevance'

def _handle_congruence_form(
    request,
    form,
    option,
    session,
    ):
    if not request.user.is_authenticated():
        raise Http403

    value = form.cleaned_data['congruence']
    if value is None:
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
    question = get_object_or_404(Question, order=question)
    relevant_sessions = \
        QuestionSessionRelevance.get_relevant_sessions(question)
    relevant_sessions = relevant_sessions[:3]
    options = list(question.option_set.all())

    for session in relevant_sessions:
        session.question_relevance = int(session.question_relevance * 100)
        option_congruences = []
        for option in options:
            user_congruence = None
            if request.user.is_authenticated():
                user_congruence = \
                    list(VoteOptionCongruence.objects.filter(option=option,
                         session=session, vote='Y', user=request.user))
                assert len(user_congruence) <= 1
                if len(user_congruence) > 0:
                    user_congruence = int(user_congruence[0].congruence * 3)
                else:
                    user_congruence = None

            data = None
            if request.method == 'POST':
                data = request.POST

            name = '%i_%i' % (session.id, option.id)
            input_form = VoteOptionCongruenceForm(data=data, prefix=name,
                    initial={'congruence': user_congruence})

            if input_form.is_valid():
                _handle_congruence_form(request, input_form, option, session)

            congruence = VoteOptionCongruence.objects.get_congruence(option, session)
            if congruence is None:
                congruence = 0
            congruence_scale = int((congruence + 1) / 2.0 * 100)

            option_congruences.append(dict(input_form=input_form,
                                      option=option,
                                      congruence_scale=congruence_scale,
                                      user_congruence=user_congruence))
        session.option_congruences = option_congruences

    args = dict(question=question, relevant_sessions=relevant_sessions)

    context_instance = RequestContext(request)
    response = render_to_response('opinions/show_question.html', args,
                                  context_instance=context_instance)

    return response


def list_questions(request):
    questions = Question.objects.all()
    parties = Party.objects.all()

    args = dict(questions=questions, parties=parties)
    return render_to_response('opinions/list_questions.html', args,
                              context_instance=RequestContext(request))


def list_questions_static(request):
    return render_to_response('opinions/list_questions_static.html', {},
                              context_instance=RequestContext(request))


@postonly
def match_session(request):
    if not request.user.is_authenticated():
        raise Http403()
    elif not request.user.has_perm(MATCH_PERM):
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
    print s
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
