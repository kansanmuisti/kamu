#!/usr/bin/python

from django.core.management import setup_environ
import sys
import os
import operator

sys.path.append(os.path.dirname(__file__) + '/../..')
sys.path.append(os.path.dirname(__file__) + '/..')

from kamu import settings

setup_environ(settings)

from django import db
from django.db import connection
from kamu.votes.models import *
from kamu.votes.views import PERIODS

def get_vote_choice(count):
        if count['Y'] > count['N']:
                return 'Y'
        elif count['Y'] < count['N']:
                return 'N'
        else: # equal
                return '?'

def tally_votes(party_list, member_list, begin, end):
    ps_list = PlenarySession.objects.between(begin, end).values_list('pk', flat=True)
    session_list = Session.objects.filter(plenary_session__in=ps_list).order_by('-plenary_session')

    pl = {}
    for party in party_list:
        pl[party.pk] = party

    ml = {}
    for member in member_list:
        ml[member.pk] = member
        member.vote_count = {}
        for v in Vote.VOTE_CHOICES:
            member.vote_count[v[0]] = 0

    idx = 0
    while len(session_list):
        sess = session_list[0]
        if idx % 50 == 0:
            print "%4d (left %d)" % (idx, len(session_list))
            db.reset_queries()

        pl_sess = sess.plenary_session

        total_count = {}
        for v in Vote.VOTE_CHOICES:
            total_count[v[0]] = 0
        for party in party_list:
            party.vote_count = {}
            for v in Vote.VOTE_CHOICES:
                party.vote_count[v[0]] = 0

        # Tally votes
        votes = Vote.objects.filter(session = sess)
        for vote in votes:
            party = pl[vote.party]
            member = ml[vote.member_id]
            party.vote_count[vote.vote] += 1
            total_count[vote.vote] += 1
            # Count total votes
            member.vote_count[vote.vote] += 1

        session_choice = get_vote_choice(total_count)
        for party in party_list:
            party.vote_choice = get_vote_choice(party.vote_count)
            if party.vote_choice == '?' or session_choice == '?':
                continue
            if not hasattr(party, "session_agree"):
                party.session_agree = { True: 0, False: 0 }
            if party.vote_choice == session_choice:
                party.session_agree[True] += 1
            else:
                party.session_agree[False] += 1

        for vote in votes:
            member = ml[vote.member_id]
            if not hasattr(member, "party_agree"):
                member.party_agree = { True: 0, False: 0 }
                member.session_agree = { True: 0, False: 0 }

            party = pl[vote.party]

            if vote.vote != 'Y' and vote.vote != 'N':
                continue

            if vote.vote == party.vote_choice:
                member.party_agree[True] += 1
            else:
                member.party_agree[False] += 1
            if vote.vote == session_choice:
                member.session_agree[True] += 1
            else:
                member.session_agree[False] += 1
        idx += 1
        session_list = session_list[1:]

def update_stats(party_list, member_list, begin, end):
    MemberStats.objects.for_period(begin, end).delete()
    for m in member_list:
        ms = MemberStats(member = m)
        ms.begin = begin
        ms.end = end
        if hasattr(m, "party_agree"):
                vcnt = []
                for v in Vote.VOTE_CHOICES:
                    vcnt.append(str(m.vote_count[v[0]]))
                ms.vote_counts = ','.join(vcnt)
                ms.party_agreement = "%d,%d" % (m.party_agree[True], m.party_agree[False])
                ms.session_agreement = "%d,%d" % (m.session_agree[True], m.session_agree[False])
        query = Statement.objects.between(begin, end).filter(member = m)
        ms.statement_count = query.count()
        ms.save()

for per in PERIODS:
    (begin, end) = (per['begin'], per['end'])
    print "%s to %s" % (begin, end)

    member_list = Member.objects.all()
    party_list = Party.objects.all()
    tally_votes(party_list, member_list, begin, end)
    update_stats(party_list, member_list, begin, end)
