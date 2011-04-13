#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import codecs
import csv
import collections
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
from django.contrib.auth.models import User


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

from opinions.models import QuestionSource, Question, Option, \
        VoteOptionCongruence, QuestionSessionRelevance

def dump_congruence(output):
    voc_list = VoteOptionCongruence.objects
    voc_list = voc_list.order_by('option__question__source__url_name',
                                 'option__question__order')
    f = open(output, mode='w')
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for voc in voc_list:
        print voc
        s1 = str(voc.option.question.source.url_name)
        s2 = str(voc.option.question.order)
        s3 = str(voc.option.order)
        s4 = str(voc.session)
        s5 = str(voc.vote)
        s6 = "%f" % voc.congruence
        s7 = str(voc.user)
        writer.writerow([s1, s2, s3, s4, s5, s6, s7])

CongEntry = collections.namedtuple('CongEntry', 'src_name, q_idx, o_idx, sess, vote, cong, user')

def import_congruence(input):
    f = open(input, mode='r')
    reader = csv.reader(f, delimiter=',', quotechar='"')
    for row in reader:
        row = CongEntry(*row)
        src = QuestionSource.objects.get(url_name=row.src_name)
        que = Question.objects.get(source=src, order=row.q_idx)
        opt = Option.objects.get(question=que, order=row.o_idx)
        sess = Session.objects.by_name(row.sess)
        try:
            user = User.objects.get(username=row.user)
        except User.DoesNotExist:
            user = None
        try:
            voc = VoteOptionCongruence.objects.get(option=opt, session=sess,
                                                   vote=row.vote, user=user)
        except VoteOptionCongruence.DoesNotExist:
            voc = VoteOptionCongruence(option=opt, session=sess, vote=row.vote,
                                       user=user)
        voc.congruence = row.cong
        voc.save()

def dump_relevance(output):
    rel_list = QuestionSessionRelevance.objects.filter(relevance__gt=0.04)
    rel_list = rel_list.order_by('question')
    f = open(output, 'w')
    writer = csv.writer(f, delimiter=',', quotechar='"')
    for rel in rel_list:
        s1 = str(rel.question.source.url_name)
        s2 = str(rel.question.order)
        s3 = str(rel.session)
        s4 = "%f" % rel.relevance
        if not rel.user:
            s5 = ''
        else:
            s5 = str(rel.user)
        writer.writerow([s1, s2, s3, s4, s5])

RelEntry = collections.namedtuple('RelEntry', 'src_name, q_idx, sess, rel, user')

def import_relevance(input):
    f = open(input, mode='r')
    reader = csv.reader(f, delimiter=',', quotechar='"')
    for row in reader:
        row = RelEntry(*row)
        src = QuestionSource.objects.get(url_name=row.src_name)
        que = Question.objects.get(source=src, order=row.q_idx)
        sess = Session.objects.by_name(row.sess)
        user = None
        if row.user:
            try:
                user = User.objects.get(username=row.user)
            except User.DoesNotExist:
                pass
        get_obj = QuestionSessionRelevance.objects.get
        try:

            rel = get_obj(option=opt, question=que, session=sess, user=user)
        except QuestionSessionRelevance.DoesNotExist:
            rel = QuestionSessionRelevance(option=opt, question=que, session=sess,
                                           user=user)
        rel.relevance = row.rel
        rel.save()


parser = OptionParser()
parser.add_option('-v', '--votes', action='store_true', dest='votes',
                  help='dump votes database')
parser.add_option('-k', '--keywords', action='store_true', dest='keywords',
                  help='dump session keywords database')
parser.add_option('-c', '--congruence', action='store_true', dest='congruence',
                  help='dump congruence database')
parser.add_option('-r', '--relevance', action='store_true', dest='relevance',
                  help='dump relevance database')
parser.add_option('-i', '--input', action='store', type='string',
                  dest='input')
parser.add_option('-o', '--output', action='store', type='string',
                  dest='output')

(opts, args) = parser.parse_args()

if opts.votes:
    dump_votes(opts.output)

if opts.keywords:
    dump_keywords(opts.output)

if opts.congruence:
    if opts.input:
        import_congruence(opts.input)
    else:
        dump_congruence(opts.output)

if opts.relevance:
    if opts.input:
#        import_congruence(opts.input)
        pass
    else:
        dump_relevance(opts.output)
