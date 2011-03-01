#!/usr/bin/python

import os
import sys
import csv
from optparse import OptionParser

from django.core.management import setup_environ

my_path = os.path.abspath(os.path.dirname(__file__))
app_path = os.path.normpath(my_path + '/..')
app_base = app_path + '/'

# We need a path like '<app_path>/utils:<app_path>:<app_path>/..'
# The first one is inserted by python itself. The order is important to
# guarantee that we'll import the proper app specific module in case there
# is also a generic (non-app-specific) module with the same name later in
# the path.
sys.path.insert(1, app_path)
sys.path.insert(2, os.path.normpath(app_path + '/..'))

from kamu import settings
setup_environ(settings)
from django.db import connection, transaction
from django import db

from votes.models import Member, TermMember, Term, MemberStats

parser = OptionParser()
parser.add_option('--input', action='store', type='string', dest='input',
                  help='input file')
(opts, args) = parser.parse_args()

if not opts.input:
    exit(1)

MEMBER_NAME_TRANSFORMS = {
    'Korhonen Timo': 'Korhonen Timo V.',
    'Ollila Heikki': 'Ollila Heikki A.',
    'Saarela Tanja': 'Karpela Tanja',
    'Kumpula Miapetra': 'Kumpula-Natri Miapetra',
    'Forsius-Harkimo Merikukka': 'Forsius Merikukka',
}

TERM="2007-2010"
term = Term.objects.get(name=TERM)

f = open(opts.input, 'r')
reader = csv.reader(f, delimiter=',', quotechar='"')
for row in reader:
    first_name = row[1].strip()
    last_name = row[0].strip()
    budget = row[4].strip().replace(',', '')
    name = "%s %s" % (last_name, first_name)
    if name in MEMBER_NAME_TRANSFORMS:
        name = MEMBER_NAME_TRANSFORMS[name]
    print "%-20s %-20s %10s" % (first_name, last_name, budget)
    try:
        member = Member.objects.get(name=name)
        tm = TermMember.objects.get(member=member, term=term)
    except Member.DoesNotExist:
        continue
    except TermMember.DoesNotExist:
        continue
    ms = MemberStats.objects.get(begin=term.begin, end=term.end, member=member)
    tm.election_budget = budget
    tm.save()
    ms.election_budget = budget
    ms.save()

f.close()

