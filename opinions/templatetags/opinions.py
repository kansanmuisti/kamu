#!/usr/bin/python
# -*- coding: utf-8 -*-
import collections

from kamu.opinions.models import Question, Option, Answer, \
    VoteOptionCongruence, QuestionSessionRelevance
from kamu.votes.models import Party, Session
from django.db import models, connection, transaction, IntegrityError
from django.utils.translation import ugettext as _
from django import forms

from django import template
register = template.Library()

CongruenceChoice = collections.namedtuple('CongruenceChoice', 'value name')
CONGRUENCE_CHOICES = (
    CongruenceChoice(str(-1.0), _('Incongruent')),
    CongruenceChoice(str(-2 / 3.0), _('Somewhat incongruent')),
    CongruenceChoice(str(-1 / 3.0), _('Slightly incongruent')),
    CongruenceChoice(str(0.0), _('Neutral/Irrelevant')),
    CongruenceChoice(str(1 / 3.0), _('Slightly congruent')),
    CongruenceChoice(str(2 / 3.0), _('Somewhat congruent')),
    CongruenceChoice(str(1.0), _('Congruent')),
    )


@register.inclusion_tag('question_session_congruence_input.html',
                        takes_context=True)
def question_session_congruence_input(context, question, session):
    request = context['request']
    option_choices = []
    for option in question.option_set.all():
        name = 'congruence_%i_%i' % (session.id, option.id)

        if name in request.POST:
            value = float(request.POST[name])
            item = VoteOptionCongruence(option=option, session=session,
                    congruence=value, vote='Y', user=request.user)
            item.save(update_if_exists=True)
            item = VoteOptionCongruence(option=option, session=session,
                    congruence=-value, vote='N', user=request.user)
            item.save(update_if_exists=True)

        if not request.user.is_anonymous():
            user_congruence = \
                VoteOptionCongruence.objects.filter(option=option,
                    session=session, vote='Y', user=request.user)
            if user_congruence.count() > 0:
                user_congruence = str(user_congruence[0].congruence)
            else:
                user_congruence = None
        else:
            user_congruence = None

        congruence = VoteOptionCongruence.get_congruence(option, session)
        if congruence is None:
            congruence = 0
        congruence_scale = int((congruence + 1) / 2.0 * 100)

        congruence_choices = CONGRUENCE_CHOICES
        option_choices.append(dict(
            option=option,
            name=name,
            congruence=congruence,
            congruence_scale=congruence_scale,
            congruence_choices=congruence_choices,
            user_congruence=user_congruence,
            ))

    return dict(question=question, session=session,
                option_choices=option_choices,
                congruence_choices=CONGRUENCE_CHOICES, user=request.user)

