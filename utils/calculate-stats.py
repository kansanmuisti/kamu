#!/usr/bin/python

from django.core.management import setup_environ
import sys
import os
import operator
import logging

sys.path.append(os.path.dirname(__file__) + '/../..')
sys.path.append(os.path.dirname(__file__) + '/..')

from kamu import settings

setup_environ(settings)

from django import db
from django.db import connection
from parliament.models import *

def get_vote_choice(count):
        if count['Y'] > count['N']:
                return 'Y'
        elif count['Y'] < count['N']:
                return 'N'
        else: # equal
                return '?'

def process_votes(pl, ml, sess):
    total_count = {}
    for v in Vote.VOTE_CHOICES:
        total_count[v[0]] = 0
    for party in party_list:
        party.vote_count = {}
        for v in Vote.VOTE_CHOICES:
            party.vote_count[v[0]] = 0

    # Tally votes
    votes = list(Vote.objects.filter(session=sess))
    for vote in votes:
        if vote.member_id not in ml:
            logger.error("Member %d not found" % vote.member_id)
        member = ml[vote.member_id]
        #if vote.party.pk not in pl:
        #    logger.warning("%s: Party '%s' not found" %
        #                 (unicode(vote), vote.party))
        party = pl[member.party.pk]
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

        party = pl[member.party.pk]

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


def tally_votes(party_list, member_list, begin, end):
    ps_list = PlenarySession.objects.between(begin, end).values_list('pk', flat=True)
    session_list = PlenaryVote.objects.filter(plsess__in=ps_list)

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
        process_votes(pl, ml, sess)
        idx += 1
        session_list = session_list[1:]


def update_stats(party_list, member_list, begin, end):
    ms_list = MemberStats.objects.filter(begin=begin, end=end)
    ms_dict = {}
    for ms in ms_list:
        ms_dict[ms.member_id] = ms
#    for q in connection.queries:
#        print q
    for m in member_list:
        if not hasattr(m, "party_agree"):
            continue
        if not m.id in ms_dict:
            ms = MemberStats(member=m, begin=begin, end=end)
        else:
            ms = ms_dict[m.id]

        vcnt = []
        for v in Vote.VOTE_CHOICES:
            vcnt.append(str(m.vote_count[v[0]]))
        ms.vote_counts = ','.join(vcnt)
        ms.party_agreement = "%d,%d" % (m.party_agree[True], m.party_agree[False])
        ms.session_agreement = "%d,%d" % (m.session_agree[True], m.session_agree[False])
        plsess = PlenarySession.objects.between(begin, end)
        query = Statement.objects.filter(item__plsess__in=plsess, member=m)
        ms.statement_count = query.count()
        ms.save()


def init_logging():
    logger = logging.getLogger("calculate_stats")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = init_logging()

for term in Term.objects.all():
    (begin, end) = (term.begin, term.end)
    print "%s to %s" % (begin, end)

    member_list = Member.objects.active_in(term.begin, term.end).select_related('party')
    party_list = Party.objects.all()
    tally_votes(party_list, member_list, begin, end)
    update_stats(party_list, member_list, begin, end)
