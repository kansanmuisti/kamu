#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_list_or_404, \
    get_object_or_404, redirect
from django.template import RequestContext
from kamu.opinions.models import *
from kamu.votes.models import Party, Session


def show_question(request, question):
    question = Question.objects.get(pk=question)
    relevant_sessions = \
        QuestionSessionRelevance.get_relevant_sessions(question)
    relevant_sessions = relevant_sessions[:3]
    for session in relevant_sessions:
        session.question_relevance = int(session.question_relevance * 100)

    args = dict(question=question, relevant_sessions=relevant_sessions)

    context_instance = RequestContext(request)
    context_instance['do_post_redirect'] = False
    response = render_to_response('show_question.html', args,
                                  context_instance=context_instance)

    # Forms are handled in form inclusion tags, so the rendering
    # has to be processed before we redirect

    if request.method == 'POST':
        return redirect(request.get_full_path())

    return response


def list_questions(request):
    questions = Question.objects.all()
    parties = Party.objects.all()

    args = dict(questions=questions, parties=parties)
    return render_to_response('list_questions.html', args,
                              context_instance=RequestContext(request))


def list_questions_static(request):
    return render_to_response('list_questions_static.html', {},
                              context_instance=RequestContext(request))


from django import template
register = template.Library()

