#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import csv
import os
import difflib

sys.path.append(os.path.abspath(__file__ + '/../../..'))
sys.path.append(os.path.abspath(__file__ + '/../..'))
from django.core.management import setup_environ
from kamu import settings
setup_environ(settings)

from kamu.opinions.models import *
from kamu.votes.models import Member


def parse_questions(input):
    questions = {}
    reader = csv.reader(input, delimiter='@')
    for row in reader:
        questions[row[0]] = row[1:]
    return questions


def get_member_match(name, choices, candidates):
    try:
        member = Member.objects.get(name=name)
        return member
    except Member.DoesNotExist:
        pass

    # return None # Comment to enable fuzzy matching....

    close = difflib.get_close_matches(name, choices, cutoff=0.8)
    close = [x for x in close if x not in candidates]
    if close:
        print('Close to %s: %s' % (name, ', '.join(close)), file=sys.stderr)

    return None


def populate_answers(input, questions, src):
    answers = list(csv.reader(input, delimiter='@'))
    allnames = map(lambda x: x.name, Member.objects.all())[:]
    candidatenames = set([x[0] for x in answers])

    members = dict([(n, get_member_match(n, allnames,
                   candidatenames)) for n in candidatenames])

    accepted = len([x for x in list(members.values()) if x is not None])
    print('Accepted %i of %i candidates' % (accepted,
            len(members)), file=sys.stderr)
    for answer in answers:
        (name, q, a, expl) = answer
        member = members[name]
        if member is None:
            continue

        try:
            qm = Question.objects.get(text=q, source=src)
        except Question.DoesNotExist:
            print("Unknown question '%s'" % q, file=sys.stderr)
            continue

        om = None
        if a:
            try:
                om = Option.objects.get(question=qm, name=a)
            except Option.DoesNotExist:
                print("Unknown option '%s' for question '%s'" \
                    % (a, q), file=sys.stderr)
                continue

        Answer.objects.get_or_create(member=member, option=om,
                                     explanation=expl)


def initialize_schema(questions, srcname, srcyear):
    (src, c) = QuestionSource.objects.get_or_create(name=srcname, year=srcyear)

    for (question, options) in list(questions.items()):
        (qm, c) = Question.objects.get_or_create(text=question, source=src)
        for option in options:
            Option.objects.get_or_create(question=qm, name=option)

    return src


def main(questionfile, answerfile):
    questions = parse_questions(questionfile)
    src = initialize_schema(questions, 'HS vaalikone', 2007)
    populate_answers(answerfile, questions, src)


if __name__ == '__main__':
    main(open(sys.argv[1], 'r'), sys.stdin)
