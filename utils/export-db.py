#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import codecs
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

import settings
setup_environ(settings)
from django.db import connection, transaction
from django import db

from votes.models import PlenarySession, Session, Vote, Term, SessionKeyword


def dump_votes(output):
    term = Term.objects.all()[0]
    pl_sess_list = PlenarySession.objects.between(term.begin, term.end)
    sess_list = Session.objects.filter(plenary_session__in=pl_sess_list)
    sess_list = sess_list.order_by('-plenary_session__date', '-number')
    f = open(output, mode="w")
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for sess in sess_list:
        print sess
        vote_list = Vote.objects.filter(session=sess).order_by('member__name').select_related('party', 'member')
        s1 = unicode(sess).encode('utf8')
        for vote in vote_list:
            s2 = unicode(vote.member).encode('utf8')
            s3 = vote.party
            s4 = str(vote.vote)
            writer.writerow([s1, s2, s3, s4])

def dump_keywords(output):
    term = Term.objects.all()[0]
    pl_sess_list = PlenarySession.objects.between(term.begin, term.end)
    sess_list = Session.objects.filter(plenary_session__in=pl_sess_list)
    sess_list = sess_list.order_by('-plenary_session__date', '-number')
    f = open(output, mode="w")
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for sess in sess_list:
        print sess
        kw_list = SessionKeyword.objects.filter(session=sess).order_by('keyword__name').select_related('keyword')
        s1 = unicode(sess).encode('utf8')
        for kw in kw_list:
            s2 = unicode(kw.keyword.name).encode('utf8')
            writer.writerow([s1, s2])

from opinions.models import VoteOptionCongruence

def dump_congruence(output):
    voc_list = VoteOptionCongruence.objects
    voc_list = voc_list.order_by('option__question__source__url_name',
                                 'option__question__order')
    f = open(output, mode="w")
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for voc in voc_list:
        print voc
        s1 = str(voc.option.question.source.url_name)
        s2 = str(voc.option.question.order)
        s3 = str(voc.session)
        s4 = str(voc.vote)
        s5 = "%f" % voc.congruence
        s6 = str(voc.user)
        writer.writerow([s1, s2, s3, s4, s5, s6])


parser = OptionParser()
parser.add_option('-v', '--votes', action='store_true', dest='votes',
                  help='dump votes database')
parser.add_option('-k', '--keywords', action='store_true', dest='keywords',
                  help='dump session keywords database')
parser.add_option('-c', '--congruence', action='store_true', dest='congruence',
                  help='dump congruence database')
parser.add_option('-o', '--output', action='store', type='string',
                  dest='output')

(opts, args) = parser.parse_args()

if opts.votes:
    dump_votes(opts.output)

if opts.keywords:
    dump_keywords(opts.output)

if opts.congruence:
    dump_congruence(opts.output)
