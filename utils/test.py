#!/usr/bin/python

from django.core.management import setup_environ
import sys
import os
import operator

sys.path.append(os.path.dirname(__file__) + '/../..')

from kamu import settings

setup_environ(settings)

from django.db import connection
from django.db.models import Q, Count
from kamu.votes.models import Member, Session, Vote, Party, MemberStats, PartyAssociation
from kamu.votes.views import PERIODS

from kamu.votes.index import complete_indexer

import djapian


mem = Member.objects.annotate(Count('statement'))
for m in mem[0:16]:
        print m
        print m.statement__count

exit(1)

mem = Member.objects.active_in('2007-01-01', '2009-01-01')
print "%d objects" % (len(mem))
for per in PERIODS[0:1]:
    for m in mem[0:4]:
        print per['query_name']
        ms = m.get_stats(per['begin'], per['end'])
        print m
        print ms
#        print m
#for pa in pa_list:
#        print pa.member_id

for q in connection.queries:
        print q
