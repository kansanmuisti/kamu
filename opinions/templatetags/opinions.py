#!/usr/bin/python
# -*- coding: utf-8 -*-
import collections

from kamu.opinions.models import Question, Option, Answer, \
    VoteOptionCongruence, QuestionSessionRelevance
from kamu.votes.models import Party, Session, Member
from kamu.user_voting import models as user_voting
from django.contrib.contenttypes.models import ContentType
from django.db import models, connection, transaction, IntegrityError
from django.utils.translation import ugettext as _
from django import forms

from django import template
register = template.Library()

@register.inclusion_tag('promise_statistics_sidebar.html',
                        takes_context=True)
def promise_statistics_sidebar(context, user):
    parties = VoteOptionCongruence.objects.get_party_congruences(for_user=user)

    member_type = ContentType.objects.get_for_model(Member)
    member_votes = user_voting.Vote.objects.filter(user=user,
                                                   content_type=member_type)
    members = []
    for vote in member_votes:
        member = Member.objects.get(pk=vote.object_id)
        member.congruence = VoteOptionCongruence.objects.get_member_congruence(
                                                            member,
                                                            for_user=user)
        if(member.congruence is None): continue
        members.append(member)
        

    return dict(parties=parties, members=members, user=user)

@register.filter
def congruence_to_percentage(share):
    if(share is None): return _("N/A")
    try:
        return "%i" % int((share+1)/2.0*100)
    except ValueError:
        return ''
