# -*- coding: utf-8 -*-
import codecs
import csv
import sys

from opinions.models import QuestionSource, Question, Option, Answer
from votes.models import Member
import http_cache
import parse_tools

CSV_URL = 'http://www.kansanmuisti.fi/storage/vaalikone/mtv2007/Eduskuntavaalikonedata_2007.csv'

OPTION_STEPS    = 7
OPTION_NAMES    = ('Täysin eri mieltä', 'Jokseenkin eri mieltä', 'Hieman eri mieltä',
		   'Ei eri eikä samaa mieltä', 'Hieman samaa mieltä', 'Jokseenkin samaa mieltä',
		   'Täysin samaa mieltä')
ANSWER_MAX      = 260


def insert_question(src, q_info):
    q_idx, i_idx, order, txt = q_info
    try:
        q = Question.objects.get(source=src, order=order)
    except Question.DoesNotExist:
        q = Question(source=src, order=order)
    q.text = txt
    q.save()

    for i in range(0, 7):
        try:
            opt = Option.objects.get(question=q, order=i)
        except Option.DoesNotExist:
            opt = Option(question=q, order=i)
        opt.name = OPTION_NAMES[i]
	opt.save()

def handle_row(src, q_info, row):
    name = parse_tools.fix_mp_name(row[0])
    mp = Member.objects.filter(name=name)
    if not mp:
        print "%s not found" % name
        return
    mp = mp[0]
    print "%s" % mp
    for q in q_info:
        q_idx, i_idx, order, txt = q
        if not row[q_idx]:
            print "\tMissing value for column %d" % q_idx
            continue
        val = int(row[q_idx])
        opt_idx = int(val * OPTION_STEPS // ANSWER_MAX)
        if opt_idx == OPTION_STEPS:
            opt_idx = OPTION_STEPS - 1
        que = Question.objects.get(source=src, order=order)
        opt = Option.objects.get(question=que, order=opt_idx)
        try:
            ans = Answer.objects.get(member=mp, question=que)
        except Answer.DoesNotExist:
            ans = Answer(member=mp, question=que)
        ans.option = opt
        ans.explanation = None
        ans.save()

def parse():
    s = http_cache.open_url(CSV_URL, 'opinions')
    src, c = QuestionSource.objects.get_or_create(name='MTV3 vaalikone', year=2007,
                                                  url_name='mtv2007')
    reader = csv.reader(s.splitlines(), delimiter=',', quotechar='"')
    reader.next()
    hdr = reader.next()
    # 2d questions
    q_list = [idx for idx, s in enumerate(hdr) if s.startswith('[2d_x]')]
    i_list = [idx for idx, s in enumerate(hdr) if s.startswith('[2d_y]')]

    # 1d questions
    q2_list = [idx for idx, s in enumerate(hdr) if s.startswith('[1d_x]')]
    q_list.extend(q2_list)
    i_list.extend([-1] * len(q2_list))

    o_list = range(0, len(q_list))

    txt_list = [hdr[idx][7:].replace('_', ',') for idx in q_list]
    for i in o_list:
        if q_list[i] in range(56, 64):
            txt_list[i] = "Hallituspuolueena " + txt_list[i]

    q_info_list = zip(q_list, i_list, o_list, txt_list)
    for q in q_info_list:
        insert_question(src, q)
    for row in reader:
        handle_row(src, q_info_list, row)

