#!/usr/bin/python
# -*- coding: utf-8 -*-

import BeautifulSoup as bs
import re
import collections
import sys
import urllib
import unicodedata
import htmllib

# NOTE:....The output needs to be tweaked manually. This script doesn't
# ....eg. strip linechanges (should have used XML instead of CSV from the start)


def strip_non_ascii(ustr):
    ustr = unicodedata.normalize('NFKD', ustr)
    return ustr.encode('ASCII', 'ignore')


def fix_whitespace(s):
    return re.sub('\s+', ' ', s)


# def unescape_html(s):
# ....p = htmllib.HTMLParser(None)
# ....p.save_bgn()
# ....p.feed(s)
# ....return p.save_end()

import htmlentitydefs


def unescape_html(text):
    """Removes HTML or XML character references 
      and entities from a text string.
   @param text The HTML (or XML) source text.
   @return The plain text, as a Unicode string, if necessary.
   from Fredrik Lundh
   2008-01-03: input only unicode characters string.
   http://effbot.org/zone/re-sub.htm#unescape-html
   """

    def fixup(m):
        text = m.group(0)
        if text[:2] == '&#':

         # character reference

            try:
                if text[:3] == '&#x':
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                print 'Value Error'
                pass
        else:

         # named entity
         # reescape the reserved characters.

            try:
                if text[1:-1] == 'amp':
                    text = '&amp;amp;'
                elif text[1:-1] == 'gt':
                    text = '&amp;gt;'
                elif text[1:-1] == 'lt':
                    text = '&amp;lt;'
                else:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is

    return re.sub("&#?\w+;", fixup, text)


def fix_input_string(s):
    s = fix_whitespace(s)
    s = unescape_html(s)
    s = s.strip()
    return s


candidatelink = collections.namedtuple('candidatelink', ('uri', 'name'))


def get_candidate_page_uris(indexpage):
    tree = bs.BeautifulSoup(indexpage)

    linkexp = 'naytaehdokas/.+?/\d+/\d+'
    links = tree.findAll('a')
    links = filter(lambda a: bool(re.search(linkexp, a['href'])), links)

    uris = map(lambda a: a['href'], links)
    uris = map(strip_non_ascii, uris)

    # uris = map(lambda u: u+'/123', uris)

    firstnames = map(lambda l: fix_input_string(l.contents[3]), links)
    lastnames = map(lambda l: fix_input_string(l.contents[2].contents[0]),
                    links)
    names = zip(lastnames, firstnames)
    links = map(lambda a: candidatelink(*a), zip(uris, names))
    return links


def parse_answers_table(table):
    options = []
    answer = None
    for (i, row) in enumerate(table.findChildren('tr')):
        cols = row.findChildren('td')
        if len(cols) < 2:
            continue
        if len(cols[1].contents) < 1:
            continue
        options.append(fix_input_string(cols[1].contents[0]))
        if cols[0].find('img'):
            assert answer is None
            answer = i

    explanation = ''
    for row in table.findChildren('span', {'class': 'pro85'}):
        row = list(row)
        if len(row) < 4:
            continue
        explanation = fix_input_string(row[3])

    return (tuple(options), answer, explanation)


candidateanswer = collections.namedtuple('candidateanswer', ('question',
        'options', 'answer', 'explanation'))


def get_candidate_answers(page):
    tree = bs.BeautifulSoup(page)
    nodes = tree.findAll('td', {'class': 'pro75', 'bgcolor': '#eeeeee'})

    nodes = filter(lambda n: len(n.contents) > 0, nodes)
    nodes = filter(lambda n: len(n.contents[0]) > 0, nodes)
    nodes = filter(lambda n: len(n.contents[0].contents) > 0, nodes)
    questions = map(lambda n: n.contents[0].contents[0].strip(), nodes)
    questions = map(fix_input_string, questions)

    answertables = map(lambda n: n.parent.findNextSibling('tr'), nodes)

    if any(map(lambda x: x is None, answertables)):
        print >> sys.stderr, 'Broken page!'
    answertables = filter(lambda a: a is not None, answertables)

    answers = map(parse_answers_table, answertables)
    qa = map(lambda a: candidateanswer(a[0], *a[1]), zip(questions, answers))
    return qa


    # print parse_answers_table(nodes[0].parent.parent.contents[2].find('table').find('tbody'))
    # print questions


def get_vaalikone_district_pages(baseaddr):
    template = baseaddr + 'listaehdokkaat.htm?ID=%i'
    ids = range(1016, 1030)
    return map(lambda i: template % i, ids)


def pretty_print_answers(answers):
    for a in answers:
        print a.question.encode('utf-8')
        for (i, opt) in enumerate(a.options):
            if a.answer == i:
                print '*',
            else:
                print ' ',
            print opt.encode('utf-8')
        print


def dump_answer_csv(candidate, answers):
    fullname = u' '.join(candidate)

    # fullname = candidate.

    for a in answers:
        if a.answer is None:
            astring = ''
        else:
            astring = a.options[a.answer]

        row = (fullname, a.question, astring, a.explanation)
        print u'@'.join(row).encode('utf-8')


def read_uri(uri, tries=3):
    for i in range(1, tries + 1):
        try:
            return urllib.urlopen(uri).read()
        except IOError, e:
            print >> sys.stderr, 'Try %i/%i failed: %s' % (i, tries, e)
    raise e


def rip_vaalikone(question_file):
    baseaddr = 'http://www3.vaalikone.fi/eduskunta2007/'
    districturis = get_vaalikone_district_pages(baseaddr)
    questions = {}
    for duri in districturis:
        dpage = urllib.urlopen(duri).read()

        # print dpage

        candidateuris = get_candidate_page_uris(dpage)
        for curi in candidateuris:
            if curi.uri.startswith('http://'):
                uri = curi.uri
            else:
                uri = baseaddr + curi.uri
            print >> sys.stderr, uri
            cpage = read_uri(uri)
            answers = get_candidate_answers(cpage)
            for a in answers:
                if a.question not in questions:
                    questions[a.question] = a.options
                else:
                    if questions[a.question] != a.options:
                        if len(a.options) > len(questions[a.question]):
                            questions[a.question] = a.options

                        # print >>sys.stderr,a.question
                        # print >>sys.stderr,a.options
                        # print >>sys.stderr,questions[a.question]

            dump_answer_csv(curi.name, answers)

    for (q, a) in questions.items():
        question_file.write(('%s@%s\n' % (q, '@'.join(a))).encode('utf-8'))


if __name__ == '__main__':
    rip_vaalikone(open(sys.argv[1], 'w'))

