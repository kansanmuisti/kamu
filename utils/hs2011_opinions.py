# -*- coding: utf-8 -*-
import codecs
import csv
import difflib
import sys
import urllib2

from opinions.models import QuestionSource, Question, Option, Answer
from votes.models import Member
import http_cache
import parse_tools

URL_BASE = 'http://www.kansanmuisti.fi/storage/vaalikone/hs2011/'
CSV_URL = URL_BASE + 'HS-vaalikone2011.csv'
OPTIONS_URL = URL_BASE + 'options.html'

ROW_HEADER = ['name', 'district', 'party', 'age', 'gender', 'edu']

# skip multiple choice questions for now
SKIP_QUESTIONS = (20, 30)

def handle_row(src, row, writer=None):
    (district, party, last_name, first_name, age, gender, is_indep) = row[0:7]
    (county, edu, intro, is_county_off, is_mp, is_mep, profession) = row[7:14]
    (home_page, rss_feed) = row[14:16]
    answer_list = row[16::3]
    importance_list = row[17::3]
    comment_list = row[18::3]

    name = ' '.join((last_name, first_name))
    name = parse_tools.fix_mp_name(name)

    if writer:
        if district.endswith(' vaalipiiri'):
            district = district.replace(' vaalipiiri', '')
        row = [name, district, party, age, gender, edu]
        row = [s.encode('utf8') if s else '' for s in row]
        writer.writerow(row)

    mp = Member.objects.filter(name=name)
    if not mp:
        if is_mp != '0':
            print name
        return
    mp = mp[0]

    for idx, ans in enumerate(answer_list):
        if idx in SKIP_QUESTIONS:
            continue
        comment = comment_list[idx]
        if not ans and not comment:
            continue
        que = Question.objects.get(source=src, order=idx)
        if ans:
            opt = Option.objects.get(question=que, name=ans)
        else:
            opt = None
        try:
            ans = Answer.objects.get(member=mp, question=que)
        except Answer.DoesNotExist:
            ans = Answer(member=mp, question=que)
        ans.option = opt
        ans.explanation = comment
        ans.save()

from lxml import etree, html

def add_question(src, qtext, q_idx, atext_list):
    if q_idx in SKIP_QUESTIONS:
        return
    try:
        q = Question.objects.get(source=src, order=q_idx)
    except Question.DoesNotExist:
        q = Question(source=src, order=q_idx)
    q.text = qtext
    q.save()

    for idx, atext in enumerate(atext_list):
        try:
            opt = Option.objects.get(question=q, order=idx)
        except Option.DoesNotExist:
            opt = Option(question=q, order=idx)
        opt.name = atext
        opt.save()

def parse_option_order(html_str, src):
    doc = html.fromstring(html_str)
    el_list = doc.xpath(".//tr[@class='question']")
    assert len(el_list) > 0
    for q_idx, el in enumerate(el_list):
        el_list = el.xpath(".//h3")
        assert len(el_list) == 1
        qtext = el_list[0].text
        el = el.getnext()
        atext_list = []
        while el.attrib.get('class') in ('even', 'odd'):
            el_list = el.xpath(".//td[@class='wide']")
            assert len(el_list) == 1
            atext = el_list[0].text
            el = el.getnext()
            atext_list.append(atext)
        add_question(src, qtext, q_idx, atext_list)

def parse():
    s = http_cache.open_url(OPTIONS_URL, 'opinions')
    src, c = QuestionSource.objects.get_or_create(name='HS vaalikone', year=2011,
                                                  url_name='hs2011')
    parse_option_order(s, src)

    s = http_cache.open_url(CSV_URL, 'opinions')
    reader = csv.reader(s.splitlines(), delimiter=',', quotechar='"')
    hdr = reader.next()
    questions = [s.decode('utf8') for s in hdr[16::3]]
    q_list = []
    for idx, q in enumerate(questions):
        if idx in SKIP_QUESTIONS:
            continue
        q_obj = Question.objects.get(source=src, text=q)
        assert q_obj.order == idx
    q_list = Question.objects.filter(source=src).order_by('order')
    writer = None
    for row in reader:
        row = [(s.decode('utf8'), None)[s == '-'] for s in row]
        handle_row(src, row, writer)

