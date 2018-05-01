# -*- coding: utf-8 -*-
import codecs
import csv
import difflib
import sys
import urllib.request, urllib.error, urllib.parse
import re

from lxml import etree, html

from . import http_cache
from . import parse_tools

from opinions.models import QuestionSource, Question, Option, Answer
from votes.models import Member, Term, DistrictAssociation

# Skip multiple answer and district-specific questions
SKIP_QUESTIONS = [30, 31, 32, 33,]

URL_BASE = "http://yle.fi/vaalikone11/index.php?emp=l-1.d-%d.s-3.q-1.ps-1"

def parse_district(district):
    base = URL_BASE % district
    s = http_cache.open_url(base, 'opinions')
    doc = html.fromstring(s)
    doc.make_links_absolute(base)

    el_list = doc.xpath(".//td[@class='em-cell-name']/a")
    cand_list = []
    for el in el_list:
        href = el.attrib['href']
        # Party links have rt-2 in them
        if '.rt-2.' in href:
            continue
        assert '.rt-1.' in href
        m = re.match(r'(\d+) ([\w -]+), ([\w \-\"\.()]+)$', el.text, re.U)
        if not m:
            print("Skipping %s" % el.text.encode('utf8'))
            continue
        last_name, first_name = m.groups()[1:]
        cand_list.append((last_name, first_name, href))
    return cand_list

# Helper code to check if we got all the answers for
# the current term MPs.
term = Term.objects.all()[0]
mp_list = list(Member.objects.active_in_term(term))
mp_dict = {}
q_dict = {}
for mp in mp_list:
    mp.found = False
    mp_dict[mp.name] = mp

def add_question(src, qtext, q_idx, atext_list):
    if not q_idx in q_dict:
        try:
            q = Question.objects.get(source=src, order=q_idx)
            assert q.text == qtext
        except Question.DoesNotExist:
            q = Question(source=src, order=q_idx)
        q.text = qtext
        q.save()
        q.opt_dict = {}
        q_dict[q_idx] = q
    else:
        q = q_dict[q_idx]
        assert q.text == qtext

    for idx, atext in enumerate(atext_list):
        if not idx in q.opt_dict:
            try:
                opt = Option.objects.get(question=q, order=idx)
                assert opt.name == atext
            except Option.DoesNotExist:
                opt = Option(question=q, order=idx)
            opt.name = atext
            opt.save()
            q.opt_dict[idx] = opt
        else:
            assert q.opt_dict[idx].name == atext
    return q

def parse_mp(src, lname, fname, href):
    name = "%s %s" % (lname, fname)
    name = parse_tools.fix_mp_name(name)
    mp = Member.objects.filter(name=name)
    if not mp:
        return
    mp = mp[0]

    if name in mp_dict:
        mp = mp_dict[name]
        mp.found = True

    print(mp)

    s = http_cache.open_url(href, 'opinions')
    doc = html.fromstring(s)
    q_list = doc.xpath(".//div[@class='em-compare-container']")
    for q_idx, q_el in enumerate(q_list):
        if q_idx in SKIP_QUESTIONS:
            continue

        el = q_el.xpath("./h3")
        assert len(el) == 1
        q_text = el[0].text.strip()
        m = re.match(r'\d+\.\s+(.+)', q_text, re.U)
        assert m
        q_text = m.groups()[0]

        a_list = q_el.xpath(".//td[@class='em-text']")
        a_text_list = []
        for a_idx, a_text in enumerate(a_list):
            a_text = a_text.text.strip()
            a_text_list.append(a_text)

        q_obj = add_question(src, q_text, q_idx, a_text_list)

        a_list = q_el.xpath(".//table[@class='em-compare-alts ']/tr")
        assert len(a_list) == len(a_text_list)
        chosen = None
        for a_idx, el in enumerate(a_list):
            if el.xpath(".//acronym"):
                assert not chosen
                chosen = a_idx
        if chosen == None:
            continue

        comm_el = q_el.xpath(".//div[@class='em-comment']")
        if comm_el:
            assert len(comm_el) == 1
            comm_el = comm_el[0]
            text_list = []
            for br in comm_el.xpath(".//br"):
                if not br.tail:
                    continue
                s = br.tail.strip()
                if s:
                    text_list.append(s)
            comm_text = '\n'.join(text_list)
            assert comm_text[0] == '"' and comm_text[-1] == '"'
            comm_text = comm_text[1:-1]
        else:
            comm_text = None

        opt = q_obj.opt_dict[chosen]
        try:
            ans = Answer.objects.get(member=mp, question=q_obj)
        except:
            ans = Answer(member=mp, question=q_obj)
        ans.option = opt
        ans.explanation = comm_text
        ans.save()

def parse():
    src, c = QuestionSource.objects.get_or_create(name='Ylen vaalikone', year=2011,
                                                  url_name='yle2011')
    for district in range(1, 16):
        print("District %d" % district)
        cand_list = parse_district(district)
        for cand in cand_list:
            parse_mp(src, *cand)
    for mp in mp_list:
        if not mp.found:
            da = DistrictAssociation.objects.for_member_in_term(mp, term)
            print("not found for %s /%s (%s)" % (mp, mp.party.name.encode('utf8'),
                da[0].name.encode('utf8')))

