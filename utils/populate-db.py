#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import sys
import os
import re
import operator
import difflib
from optparse import OptionParser

from BeautifulSoup import BeautifulSoup
from lxml import etree, html

import vote_list_parser
import mop_list_parser
import mop_info_parser
import party_list_parser
import party_info_parser
import minutes_parser

import http_cache
from http_cache import create_path_for_file

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

import kamu.votes.models
from kamu.votes.models import *

until_pl = None
from_pl = None

TERM_DASH = u'\u2013'
TERMS = [
    {'display_name': '2011'+TERM_DASH+'2014', 'begin': '2011-04-20', 'end': None,
     'name': '2011-2014'},
    {'display_name': '2007'+TERM_DASH+'2010', 'begin': '2007-03-21', 'end': '2011-04-19',
     'name': '2007-2010'},
    {'display_name': '2003'+TERM_DASH+'2006', 'begin': '2003-03-19', 'end': '2007-03-20',
     'name': '2003-2006'},
    {'display_name': '1999'+TERM_DASH+'2002', 'begin': '1999-03-24', 'end': '2003-03-18',
     'name': '1999-2002', 'visible': False},
]

term_list = Term.objects.all()
def fill_terms():
    for term in TERMS:
        try:
            nt = Term.objects.get(name=term['name'])
        except Term.DoesNotExist:
            print(u'Adding term %s' % term['display_name'])
            nt = Term()
        nt.name = term['name']
        nt.begin = term['begin']
        nt.end = term['end']
        nt.display_name = term['display_name']
        if 'visible' in term:
            nt.visible = term['visible']
        nt.save()

    global term_list
    terms = Term.objects.all()

static_path = app_base + 'static/'

url_base = 'http://www.eduskunta.fi'
mp_photo_path = 'images/members/'
party_logo_path = 'images/parties/'

party_url_base = 'http://web.eduskunta.fi'
party_list_url = '/Resource.phx/eduskunta/organisaatio/kansanedustajat/kansanedustajateduskuntaryhmittain.htx'

mp_list_url = '/triphome/bin/thw/trip/?${base}=hetekaue&${maxpage}=10001&${snhtml}=hex/hxnosynk&${html}=hex/hx4600&${oohtml}=hex/hx4600&${sort}=lajitnimi&nykyinen=$+and+vpr_alkutepvm%3E=22.03.1991'
heti_url = '/triphome/bin/hex5000.sh?hnro=%s&kieli=su'

STAT_URL_BASE = 'http://www.stat.fi'
STAT_COUNTY_URL = '/meta/luokitukset/vaalipiiri/001-2011/luokitusavain_kunta_teksti.txt'
# STAT_COUNTY_URL = '/meta/luokitukset/vaalipiiri/001-2007/luokitusavain_teksti.txt'

KEYWORD_URL_BASE = 'http://www.eduskunta.fi'
KEYWORD_LIST_URL = '/triphome/bin/vex6000.sh'

def process_parties(db_insert):
    s = http_cache.open_url(party_url_base + party_list_url, 'party')
    parser = party_list_parser.Parser()
    parser.feed(s)
    parser.close()
    party_list = parser.get_list()
    parser = party_info_parser.Parser()
    for party in party_list:
        s = http_cache.open_url(party_url_base + party['info_link'], 'party')
        parser.reset()
        parser.feed(s)
        parser.close()
        party.update(parser.get_desc())

        logo_url = party_url_base + party['logo']
        fname = party['name'].encode('iso8859-1') + '.jpg'
        party['logo'] = fname
        fname = static_path + party_logo_path + fname
        create_path_for_file(fname)
        if not os.path.exists(fname):
            print 'Fetching logo ' + logo_url
            s = http_cache.open_url(logo_url, 'party')
            f = open(fname, 'wb')
            f.write(s)
            f.close()
        else:
            print 'Skipping logo ' + party['logo']

        if not db_insert:
            continue

        try:
            p = Party.objects.get(name=party['name'])
        except Party.DoesNotExist:
            p = None
        if not p:
            p = Party()
            p.name = party['name']
        p.full_name = party['fullname']
        p.logo = party_logo_path + party['logo']
        p.info_link = party_url_base + party['info_link']
        p.save()

    return party_list


def find_party(party_list, fname):
    for party in party_list:
        if party['fullname'] == fname:
            return party['name']
    return None


def process_mops(party_list, update=False, db_insert=False):
    s = http_cache.open_url(url_base + mp_list_url, 'member')
    BAD_HTML = '<! hx4600.thw>'
    idx = s.find(BAD_HTML)
    if idx >= 0:
        s = s[idx + len(BAD_HTML) + 1:]
    parser = mop_list_parser.Parser()
    parser.feed(s)
    parser.close()
    mop_list = parser.get_mop_list()

    parser = mop_info_parser.Parser()
    for mp in mop_list:
        print '%3d: %s, %s' % (mop_list.index(mp), mp['surname'],
                               mp['firstnames'])
        s = http_cache.open_url(url_base + mp['link'], 'member')
        parser.reset(is_lame_frame=True)
        parser.feed(s)
        parser.close()
        mp.update(parser.get_desc())

        print '%3d: person number %s' % (mop_list.index(mp), mp['hnro'])

        try:
            member = Member.objects.get(pk=mp['hnro'])
        except Member.DoesNotExist:
            member = None

        if member and not update:
            continue

        s = http_cache.open_url(url_base + heti_url % mp['hnro'],
                                'member')
        parser.reset(is_lame_frame=False)
        parser.feed(s)
        parser.close()
        mp.update(parser.get_desc())

        photo_url = url_base + mp['photo']

        ext = os.path.splitext(mp['photo'])[-1]
        fname = hashlib.sha1(mp['name'].encode('iso8859-1')).hexdigest()
        mp['photo'] = fname + ext
        photo_fname = static_path + mp_photo_path + mp['photo']
        create_path_for_file(photo_fname)
        if not os.path.exists(photo_fname):
            print 'Fetching photo ' + photo_url
            s = http_cache.open_url(photo_url, 'member')
            f = open(photo_fname, 'wb')
            f.write(s)
            f.close()
        else:
            print 'Skipping photo ' + mp['photo']

        party_name = None
        if 'party' in mp:
            party_name = find_party(party_list, mp['party'])
            if not party_name:
                raise Exception('Unknown party')

        for assoc in mp['assoc']:
            if 'end' not in assoc:
                end = None
            else:
                end = assoc['end']
            party = find_party(party_list, assoc['name'])
            if party == None:
                if not end:
                    print assoc
                    raise Exception('party not found')
                    # FIXME: Maybe add the party?
                assoc['name'] = None
            else:
                assoc['name'] = party

        # Find last party association
        last_assoc = sorted(mp['assoc'], key=operator.itemgetter('start'))[-1]
        if 'end' in last_assoc:
            if party_name:
                raise Exception('party set for inactive MP')
            party_name = last_assoc['name']

        if not db_insert:
            continue

        if not member:
            member = Member()
            member.id = mp['hnro']
        member.name = mp['name']
        member.party_id = party_name
        member.photo = mp_photo_path + mp['photo']
        member.info_link = url_base + heti_url % mp['hnro']
        member.birth_date = mp['birthdate']
        member.given_names = mp['firstnames']
        member.surname = mp['surname']
        if 'phone' in mp:
            member.phone = mp['phone']
        if 'email' in mp:
            member.email = mp['email']
        member.save()

        PartyAssociation.objects.filter(member=member).delete()
        for assoc in mp['assoc']:
            if not assoc['name']:
                continue
            if 'end' not in assoc:
                end = None
            else:
                end = assoc['end']
            party = Party.objects.get(name=assoc['name'])
            pa = PartyAssociation()
            pa.member = member
            pa.party_id = party.pk
            pa.begin = assoc['start']
            pa.end = end
            pa.save()
        DistrictAssociation.objects.filter(member=member).delete()
        for assoc in mp['district']:
            if 'end' not in assoc:
                end = None
            else:
                end = assoc['end']
            da = DistrictAssociation()
            da.member = member
            da.name = assoc['name']
            da.begin = assoc['start']
            da.end = end
            da.save()

    return mop_list

def get_mp_homepage_link(mp, force_update=False):
    if mp.homepage_link and not force_update:
        return
    s = http_cache.open_url(mp.wikipedia_link, 'misc')
    doc = html.fromstring(s)
    b = doc.xpath(".//b[.='Kotisivu']")
    if not b:
        return
    elem = b[0].getparent()
    href = elem.getnext().getchildren()[0].attrib['href']
    print "%s: %s" % (mp.name, href)
    # Try to fetch the homepage
    s = http_cache.open_url(href, 'misc', skip_cache=True, error_ok=True)
    if s:
        mp.homepage_link = href
    else:
        print "\tFailed to fetch"

def get_wikipedia_links():
    MP_LINK = 'http://fi.wikipedia.org/wiki/Luokka:Nykyiset_kansanedustajat'

    print "Populating Wikipedia links to MP's..."
    mp_list = Member.objects.all()
    mp_names = [mp.name for mp in mp_list]
    s = http_cache.open_url(MP_LINK, 'misc')
    doc = html.fromstring(s)
    links = doc.xpath(".//table//a[starts-with(@href, '/wiki')]")
    doc.make_links_absolute(MP_LINK)
    for l in links:
        href = l.attrib['href']
        if 'Toiminnot:Haku' in href:
            continue
        name = l.text
        if '(' in name:
            name = name.split('(')[0].strip()
        a = name.split()
        a = list((a[-1],)) + a[0:-1]
        name = ' '.join(a)
        try:
            mp = Member.objects.get(name=name)
        except Member.DoesNotExist:
            matches = difflib.get_close_matches(name, mp_names, cutoff=0.8)
            if len(matches) > 1:
                raise Exception("Multiple matches for '%s'" % name)
            print("Mapping '%s' to %s'" % (name, matches[0]))
            mp = Member.objects.get(name=matches[0])
        mp.wikipedia_link = href
        get_mp_homepage_link(mp)
        mp.save()

def process_mp_terms():
    for mp in Member.objects.all():
        # Check if MP was active during a term.
        for term in Term.objects.all():
            q = DistrictAssociation.objects.between(term.begin, term.end)
            q = q.filter(member=mp)
            if q:
                try:
                    tm = TermMember.objects.get(term=term, member=mp)
                except TermMember.DoesNotExist:
                    tm = TermMember(term=term, member=mp)
                    tm.save()
            else:
                try:
                    tm = TermMember.objects.get(term=term, member=mp).delete()
                except TermMember.DoesNotExist:
                    pass

def process_counties(db_insert):
    s = http_cache.open_url(STAT_URL_BASE + STAT_COUNTY_URL, 'county')

    # strip first 4 lines of header and any blank/empty lines at EOF
    for line in s.rstrip().split('\n')[4:]:
        dec_line = line.decode('iso8859-1').rstrip().split('\t')
        (county_id, county_name, district_id, district_name) = dec_line

        if not db_insert:
            continue

        try:
            c = County.objects.get(name=county_name)
        except:
            c = None
        if not c:
            c = County()
            c.name = county_name
        c.district = district_name
        c.save()

def insert_keyword(kword, max_len, trim_re):
    if not kword.a:                                   # is there a hyper-link?
        return
    # skip keywords with a class defined -- they're not real keywords
    for c in kword.attrs:
        if c[0] == 'class':
            return
    kword_str = unicode(kword.contents[0].string)
    kword_str = trim_re.sub('', kword_str)            # strip any trailing ' ]'
    kword_str = kword_str[:max_len]

    try:
        k = Keyword.objects.get(name=kword_str)
    except Keyword.DoesNotExist:
        k = Keyword()
        k.name = kword_str
        k.save()

def process_keywords():
    mpage = http_cache.open_url(KEYWORD_URL_BASE + KEYWORD_LIST_URL, 'keyword')
    # BeautifulSoup's SGML parser will break at the following pattern,
    # so remove it before handing over for parsing
    pat = 'document.write\("<SCR"\+"IPT Language=.JavaScript. SRC=."\+"' +  \
          'http://"\+gDomain\+"/"\+gDcsId\+"/wtid.js"\+".></SCR"\+"IPT>"\);'

    massage = [(re.compile(pat), lambda match: '')]
    dir_soup = BeautifulSoup(mpage, markupMassage=massage,
                             fromEncoding='iso-8859-1',
                             convertEntities=BeautifulSoup.HTML_ENTITIES)
    dir_list = dir_soup.find('p', text='A) Valitse asiasana aakkosittain'). \
                          parent.findNextSiblings('a')

    max_len = Keyword._meta.get_field_by_name('name')[0].max_length
    trim_re = re.compile(' \[$')
    for dir_elem in dir_list:
        kpage_url = KEYWORD_URL_BASE + dir_elem['href']
        kpage = http_cache.open_url(kpage_url, 'keyword')
        ksoup = BeautifulSoup(kpage, markupMassage=massage,
                              fromEncoding='iso-8859-1',
                              convertEntities=BeautifulSoup.HTML_ENTITIES)
        anchor = ksoup.find('p', text=' Suorita haku asiasanalla:')
        elem = anchor.parent.parent.nextSibling.nextSibling
        kword_list = elem.findAll('li')
        for kword in kword_list:
            insert_keyword(kword, max_len, trim_re)

# VOTE_URL = "/triphome/bin/aax3000.sh?kanta=&PALUUHAKU=%2Fthwfakta%2Faanestys%2Faax%2Faax.htm&" +\
#           "haku=suppea&VAPAAHAKU=&OTSIKKO=&ISTUNTO=&AANVPVUOSI=(2007%2Bor%2B2008%2Bor%2B2009%2Bor%2B2010)&PVM1=&PVM2=&TUNNISTE="

# VOTE_URL = "/triphome/bin/aax3000.sh?kanta=&PALUUHAKU=%2Fthwfakta%2Faanestys%2Faax%2Faax.htm&" +\
#           "haku=suppea&VAPAAHAKU=&OTSIKKO=&ISTUNTO=&AANVPVUOSI=(2003%2Bor%2B2004%2Bor%2B2005%2Bor%2B2006)&PVM1=&PVM2=&TUNNISTE="

VOTE_URL = '/triphome/bin/aax3000.sh?VAPAAHAKU=aanestysvpvuosi=%i'
MINUTES_URL = '/triphome/bin/akx3000.sh?kanta=utaptk&LYH=LYH-PTK&haku=PTKSUP&kieli=su&VPVUOSI>=1999'
BEGIN_YEAR = 1999
END_YEAR = 2010

def read_links(is_minutes, url, new_only=False):
    if is_minutes:
        link_type = 'minutes'
    else:
        link_type = 'votes'

    ret = []

    while True:
        s = http_cache.open_url(url, link_type, new_only)
        doc = html.fromstring(s)
        votes = doc.xpath(".//div[@class='listing']/div/p")
        doc.make_links_absolute(url)

        for vote in votes:
            link = {}

            links = vote.xpath('.//a')

            minutes_link = [l for l in links if '/akxptk.sh?' in l.attrib['href']]
            if len(minutes_link) != 1:
                print http_cache.get_fname(url, link_type)
                raise Exception("Unable to find link to minutes")
            link['minutes'] = minutes_link[0].attrib['href']
            if is_minutes:
                pls_name = vote.getchildren()[0].text.strip()
                m = re.match(r"PTK (\w+/\d{4}) vp", pls_name)
                link['plsess'] = m.group(1)
            else:
                link['plsess'] = minutes_link[0].text.strip()[4:-3]
                b_elem = minutes_link[0].getnext()
                if b_elem.tag != 'b':
                    print http_cache.get_fname(url, link_type)
                    raise Exception("Unexpected <b> tag")
                nr = int(b_elem.text.strip()[10:].strip().split()[1])
                link['number'] = nr
                link_list = [l for l in links if '=aax/aax5000&' in l.attrib['href']]
                if len(link_list) != 1:
                    raise Exception("Unable to find vote results")
                link['results'] = link_list[0].attrib['href']

                link_list = [l for l in links if '/vex3000.sh?' in l.attrib['href']]
                if len(link_list) != 1:
                    print >> sys.stderr, 'Warning: Vote does not have keyword info'
                else:
                    link['info'] = link_list[0].attrib['href']

            ret.append(link)

        # Check if last page of links
        if len(votes) >= 50:
            fwd_link = doc.xpath(".//input[@name='forward']")
            url = url_base + fwd_link[0].attrib['value']
        else:
            url = None
            break
        if new_only:
            break

    return (ret, url)

pl_sess_list = {}
mem_name_list = {}

@transaction.commit_manually
def process_session_votes(url, pl_sess_name):
    parser = vote_list_parser.Parser()
    s = http_cache.open_url(url, 'votes')
    parser.reset()
    parser.feed(s)
    parser.close()
    votes = parser.get_votes()
    desc = parser.get_desc()

    desc['nr'] = int(desc['nr'])
    desc['pl_session'] = pl_sess_name

    if pl_sess_name in pl_sess_list:
        pl_sess = pl_sess_list[pl_sess_name]
    else:
        try:
            pl_sess = PlenarySession.objects.get(name=pl_sess_name)
        except PlenarySession.DoesNotExist:
            pl_sess = PlenarySession(name=pl_sess_name)
            pl_sess_list[pl_sess_name] = pl_sess
        pl_sess.date = desc['date']
        pl_sess.term = Term.objects.get_for_date(pl_sess.date)
        pl_sess.info_link = url_base + desc['session_link']
        pl_sess.save()

    # If the plenary session was deleted, all the child
    # objects were, too.
    try:
        sess = Session.objects.get(plenary_session=pl_sess, number=desc['nr'])
    except Session.DoesNotExist:
        sess = Session(plenary_session=pl_sess, number=desc['nr'])
    sess.time = desc['time']
    sess.info = '\n'.join(desc['info'])
    sess.subject = desc['subject']
    sess.info_link = None
    sess.save()

    sess.sessiondocument_set.clear()
    for doc in desc['docs']:
        name = doc[0]
        try:
            sd = SessionDocument.objects.get(name=name)
        except SessionDocument.DoesNotExist:
            sd = SessionDocument(name=name)
            sd.info_link = url_base + doc[1]
            sd.save()
        sd.sessions.add(sess)

    sess.vote_set.all().delete()
    for v in votes:
        vote = Vote()
        vote.session = sess
        vote.member_name = v[0]
        vote.party = v[1]
        vote.vote = v[2]
        if not vote.member_name in mem_name_list:
            member = Member.objects.get(name=vote.member_name)
            mem_name_list[vote.member_name] = member
        vote.member = mem_name_list[vote.member_name]
        vote.save()

    sess.count_votes()
    sess.save()

    transaction.commit()
    db.reset_queries()

    return sess

def process_session_keywords(sess, url):
    s = http_cache.open_url(url, 'votes')
    doc = html.fromstring(s)
    kw_list = doc.xpath(".//div[@id='vepsasia-asiasana']//div[@class='linkspace']/a")

    for kw in kw_list:
        kw = kw.text.strip()
        print '\t%s' % kw
        try:
            kw_obj = Keyword.objects.get(name=kw)
        except Keyword.DoesNotExist:
            import codecs
            f = codecs.open('new-kws.txt', 'a', 'utf-8')
            f.write(u'%s\n' % kw)
            f.close()
            kw_obj = Keyword(name=kw)
            kw_obj.save()
        SessionKeyword.objects.get_or_create(session=sess, keyword=kw_obj)

def process_votes(full_update=False, verify=False):
    start_from = from_pl
    year = END_YEAR
    next_link = None
    stop_after = None
    processed_sess_list = []
    while True:
        if not next_link:
            next_link = url_base + VOTE_URL % year
        (sess_list, next_link) = read_links(False, next_link, not full_update)
        print 'Got links for total of %d sessions' % len(sess_list)
        for sess_desc in sess_list:
            sess = Session.objects.filter(plenary_session=sess_desc['plsess'],
                                          number=sess_desc['number'])
            if sess:
                assert len(sess) == 1
                sess = sess[0]

            idx = sess_list.index(sess_desc)
            print '%4d. Vote %d / %s' % (idx, sess_desc['number'], sess_desc['plsess'])
            if start_from:
                if start_from == sess_desc['plsess']:
                    start_from = None
                else:
                    continue
            if stop_after and sess_desc['plsess'] != stop_after:
                return processed_sess_list
            processed_sess_list.append(sess)
            if verify:
                continue
            if not full_update and sess:
                # If the session doesn't have keywords, we process only those.
                if not sess.sessionkeyword_set.all():
                    if 'info' in sess_desc:
                        process_session_keywords(sess, sess_desc['info'])
                        continue
                else:
                    return processed_sess_list

            sess = process_session_votes(sess_desc['results'], sess_desc['plsess'])
            # Process keywords
            if 'info' in sess_desc:
                process_session_keywords(sess, sess_desc['info'])
            if until_pl and sess_desc['plsess'] == until_pl:
                stop_after = until_pl

        if not next_link:
            year -= 1
            if year < BEGIN_YEAR:
                break
    return processed_sess_list

def process_session_kws():
    year = END_YEAR
    next_link = None
    while True:
        if not next_link:
            next_link = url_base + VOTE_URL % year
        (vote_links, next_link) = read_links(False, next_link, False)
        print 'Got links for total of %d sessions' % len(vote_links)
        for link in vote_links:
            nr = vote_links.index(link)

def insert_minutes(minutes):
    mins = None
    try:
        pl_sess = PlenarySession.objects.get(name=minutes['id'])
    except PlenarySession.DoesNotExist:
        pl_sess = PlenarySession()
        pl_sess.name = minutes['id']
        pl_sess.date = minutes['date']
        pl_sess.term = Term.objects.get_for_date(pl_sess.date)
        pl_sess.info_link = minutes['url']
        pl_sess.save()

    mins = Minutes()
    mins.plenary_session = pl_sess
    mins.html = minutes['html']
    mins.save()

    return pl_sess


OK_UNKNOWNS = ['Alexander Stubb', u'Petri J\u00e4\u00e4skel\u00e4inen',
               'Jaakko Jonkka', 'Riitta-Leena Paunio']


def insert_discussion(full_update, pl_sess, disc, dsc_nr, members):
    idx = 0
    for spkr in disc:
        if not spkr['name'] in members:
            if not spkr['name'] in OK_UNKNOWNS:
                print spkr['name']
                raise Exception('Unknown member: ' + spkr['name'])
            member = None
        else:
            member = members[spkr['name']]
        idx = disc.index(spkr)
        try:
            st = Statement.objects.get(plenary_session=pl_sess,
                                       dsc_number=dsc_nr, index=idx)
            if not full_update:
                return False
        except Statement.DoesNotExist:
            st = Statement()
            st.plenary_session = pl_sess
            st.index = idx
            st.dsc_number = dsc_nr
        st.member = member
        st.text = '\n'.join(spkr['statement'])
        match = False
        for n in st.text:
            OK = [225, 224, 189, 232, 237, 352, 248, 201, 180, 233, 196,
                  214, 252, 229, 197, 167, 353, 228, 160, 246, 250, 8230,
                  243, 235, 244, 231]
            if ord(n) >= 128 and ord(n) not in OK:
                print '%d: %c' % (ord(n), n)
                start = st.text.index(n) - 20
                if start < 0:
                    start = 0
                print st.text[start:]
                match = True
        st.html = spkr['html']
        st.save()
    return True


@transaction.commit_manually
def process_minutes(full_update):
    start_from = from_pl
    stop_after = None
    member_list = Member.objects.all()
    member_dict = {}
    for mem in member_list:
        (last, first) = mem.name.split(' ', 1)
        name = ' '.join((first, last))
        if name in member_dict:
            raise Exception()
        member_dict[name] = mem

    next_link = url_base + MINUTES_URL
    while next_link:
        (links, next_link) = read_links(True, next_link, new_only=not full_update)
        print 'Got links for total of %d minutes' % len(links)
        for link in links:
            url = link['minutes']
            print '%4d. %s' % (links.index(link), link['plsess'])
            if start_from:
                if link['plsess'] == start_from:
                    start_from = None
                else:
                    continue
            if stop_after and sess_desc['plsess'] != stop_after:
                return
            s = http_cache.open_url(url, 'minutes')
            tmp_url = 'http://www.eduskunta.fi/faktatmp/utatmp/akxtmp/'
            minutes = minutes_parser.parse_minutes(s, tmp_url)
            if not minutes:
                continue
            minutes['url'] = url
            try:
                mins = Minutes.objects.get(plenary_session__name=link['plsess'])
                if not full_update:
                    return
            except Minutes.DoesNotExist:
                pass
            pl_sess = insert_minutes(minutes)
            try:
                for l in minutes['cnv_links']:
                    print l
                    s = http_cache.open_url(l, 'minutes')
                    disc = minutes_parser.parse_discussion(s, l)
                    insert_discussion(full_update, pl_sess, disc,
                                      minutes['cnv_links'].index(l),
                                      member_dict)
            except:
                Minutes.objects.get(plenary_session=pl_sess).delete()
                Statement.objects.filter(plenary_session=pl_sess).delete()
                raise
            transaction.commit()
            db.reset_queries()
            if until_pl and link['plsess'] == until_pl:
                stop_after = until_pl

HE_URL = "http://217.71.145.20/TRIPviewer/temp/TUNNISTE_HE_%i_%i_fi.html"

def process_doc(doc):
    hematch = re.compile('HE (\d+)/(\d{4})')
    match = hematch.match(doc.name)
    number, year = map(int, match.groups())
    url = HE_URL % (number, year)

    s = http_cache.open_url(url, 'docs', error_ok=True)
    if not s:
        (s, url) = http_cache.open_url(doc.info_link, 'docs', return_url=True)
        if '<!-- akxereiloydy.thw -->' in s or '<!-- akx5000.thw -->' in s:
            print "\tNot found!"
            return
        html_doc = html.fromstring(s)
        frames = html_doc.xpath(".//frame")
        link_elem = None
        for f in frames:
            if f.attrib['src'].startswith('temp/'):
                link_elem = f
                break
        html_doc.make_links_absolute(url)
        url = link_elem.attrib['src']
        print "\tGenerated and found!"
        s = http_cache.open_url(url, 'docs')
    # First check if's not a valid HE doc, the surest way to
    # detect it appears to be the length. *sigh*
    if len(s) < 1500:
        print "\tJust PDF"
        return
    html_doc = html.fromstring(s)
    elem_list = html_doc.xpath(".//p[@class='Normaali']")

    ELEM_CL = ['LLEsityksenPaaSis',
               'LLEsityksenp-00e4-00e4asiallinensis-00e4lt-00f6',
               'LLVSEsityksenp-00e4-00e4asiallinensis-00e4lt-00f6',
               'LLPaaotsikko']
    for cl in ELEM_CL:
        elem = html_doc.xpath(".//p[@class='%s']" % cl)
        if elem:
            break
    if not elem:
        print "\tNo header found: %d" % len(s)
        print http_cache.get_fname(url, 'docs')
        return
    # Choose the first header. Sometimes they are replicated. *sigh*
    elem = elem[0].getnext()
    p_list = []
    if 'class' in elem.attrib and elem.attrib['class'] == 'LLNormaali' and \
            elem.getnext().attrib['class'] == 'LLKappalejako':
        elem = elem.getnext()
    while elem is not None:
        if elem.tag != 'p':
            print elem.tag
            break
        OK_CLASS = ('LLKappalejako', 'LLJohtolauseKappaleet',
                    'LLVoimaantulokappale',
                    'LLKappalejako-0020Char-0020Char-0020Char', # WTF
        )
        if not 'class' in elem.attrib or elem.attrib['class'] not in OK_CLASS:
            break
        p_list.append(elem)
        elem = elem.getnext()
    BREAK_CLASS = ('LLNormaali', 'LLYleisperustelut', 'LLPerustelut',
                   'LLNormaali-0020Char', 'Normaali', 'LLSisallysluettelo')
    if 'class' in elem.attrib and elem.attrib['class'] not in BREAK_CLASS:
        print "\tMystery class: %s" % elem.attrib
        print http_cache.get_fname(url, 'docs')
        return
    if not p_list:
        print "\tNo summary found"
        print http_cache.get_fname(url, 'docs')
        return
    text_list = []

    def append_text(elem, no_append=False):
        text = ''
        if elem.text:
            text = elem.text.replace('\r', '').replace('\n', '').strip()
            text = text.replace('&nbsp;', '')
        if elem.getchildren():
            for ch in elem.getchildren():
                text += append_text(ch, no_append=True)
        if len(text) < 15 and u'\u2014' in text:
            return
        if no_append:
            return text
        text = text.strip()
        if text:
            text_list.append(text)

    for p in p_list:
        append_text(p)
    mark = False
    for t in text_list:
        if len(t) < 15:
            mark = True
            break
    if mark:
        print http_cache.get_fname(url, 'docs')
        for t in text_list:
            print t
        return
    doc.summary = '\n'.join(text_list)
    doc.save()

def process_session_docs(full_update):
    doc_list = SessionDocument.objects.filter(name__startswith='HE')
    doc_list = list(doc_list)
    for doc in doc_list:
        if doc.summary and not full_update:
            continue
        print "%s: %s" % (doc_list.index(doc), doc.name)
        if not doc.info_link:
            continue
        process_doc(doc)

def verify_sessions():
    found_sess_list = process_votes(full_update=True, verify=True)
    found_sess_dict = {}
    for sess in found_sess_list:
        found_sess_dict[str(sess)] = sess
    sess_list = list(Session.objects.all())
    for sess in sess_list:
        if str(sess) not in found_sess_dict:
            print str(sess)

parser = OptionParser()
parser.add_option('-p', '--parties', action='store_true', dest='parties',
                  help='populate party database')
parser.add_option('-m', '--members', action='store_true', dest='members',
                  help='populate member database')
parser.add_option('-c', '--counties', action='store_true', dest='counties',
                  help='populate counties database')
parser.add_option('-v', '--votes', action='store_true', dest='votes',
                  help='populate vote database')
parser.add_option('-M', '--minutes', action='store_true', dest='minutes',
                  help='populate session minutes database')
parser.add_option('-k', '--keywords', action='store_true', dest='keywords',
                  help='populate voting keywords database')
parser.add_option('-d', '--docs', action='store_true', dest='docs',
                  help='populate session documents')
parser.add_option('--verify-sessions', action='store_true', dest='verify_sessions',
                  help='verify session list')
parser.add_option('--cache', action='store', type='string', dest='cache',
                  help='use cache in directory CACHE')
parser.add_option('--full-update', action='store_true', dest='full_update',
                  help='perform a full database update')
parser.add_option('--until-pl', action='store', type='string', dest='until_pl',
                  help='process until named plenary session reached')
parser.add_option('--from-pl', action='store', type='string', dest='from_pl',
                  help='process starting from named plenary session')

(opts, args) = parser.parse_args()

party_list = None
if opts.cache:
    http_cache.set_cache_dir(opts.cache)
if opts.until_pl:
    until_pl = opts.until_pl
if opts.from_pl:
    from_pl = opts.from_pl
if opts.parties or opts.members:
    party_list = process_parties(True)
    fill_terms()

if opts.members:
    mp_list = process_mops(party_list, True, True)
    get_wikipedia_links()
    process_mp_terms()

if opts.counties:
    counties = process_counties(True)
if opts.votes:
    process_votes(opts.full_update)
if opts.minutes:
    process_minutes(opts.full_update)
if opts.keywords:
    process_keywords()
if opts.docs:
    process_session_docs(opts.full_update)
if opts.verify_sessions:
    verify_sessions()
