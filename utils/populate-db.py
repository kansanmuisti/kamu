#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import cookielib
import time
import sys
import os
import re
import sqlite3
import hashlib
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

cache_dir = None
until_pl = None

TERM_DASH = u'\u2013'
TERMS = [
    {'display_name': '2007'+TERM_DASH+'2010', 'begin': '2007-03-21', 'end': None,
     'name': '2007-2010' },
    {'display_name': '2003'+TERM_DASH+'2006', 'begin': '2003-03-19', 'end': '2007-03-20',
     'name': '2003-2006' },
#    {'display_name': '1999'+TERM_DASH+'2002', 'begin': '1999-03-24', 'end': '2003-03-18',
#     'name': '1999-2002' },
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
        nt.save()

    global term_list
    terms = Term.objects.all()

def create_path_for_file(fname):
    dirname = os.path.dirname(fname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def get_cache_fname(url, prefix):
    hash = hashlib.sha1(url.replace('/', '-')).hexdigest()
    fname = '%s/%s/%s' % (cache_dir, prefix, hash)
    return fname

def open_url_with_cache(url, prefix, skip_cache=False, error_ok=False):
    fname = None
    if cache_dir and not skip_cache:
        fname = get_cache_fname(url, prefix)
    if not fname or not os.access(fname, os.R_OK):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        try:
            f = opener.open(url)
        except urllib2.URLError:
            if error_ok:
                return None
            raise
        s = f.read()
        if fname:
            create_path_for_file(fname)
            outf = open(fname, 'w')
            outf.write(s)
            outf.close()
    else:
        f = open(fname)
        s = f.read()
    f.close()

    return s


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
    s = open_url_with_cache(party_url_base + party_list_url, 'party')
    parser = party_list_parser.Parser()
    parser.feed(s)
    parser.close()
    party_list = parser.get_list()
    parser = party_info_parser.Parser()
    for party in party_list:
        s = open_url_with_cache(party_url_base + party['info_link'], 'party')
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
            s = open_url_with_cache(logo_url, 'party')
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
    s = open_url_with_cache(url_base + mp_list_url, 'member')
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
        s = open_url_with_cache(url_base + mp['link'], 'member')
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

        s = open_url_with_cache(url_base + heti_url % mp['hnro'],
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
            s = open_url_with_cache(photo_url, 'member')
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
    s = open_url_with_cache(mp.wikipedia_link, 'misc')
    doc = html.fromstring(s)
    b = doc.xpath(".//b[.='Kotisivu']")
    if not b:
        return
    elem = b[0].getparent()
    href = elem.getnext().getchildren()[0].attrib['href']
    print "%s: %s" % (mp.name, href)
    # Try to fetch the homepage
    s = open_url_with_cache(href, 'misc', skip_cache=True, error_ok=True)
    if s:
        mp.homepage_link = href
    else:
        print "\tFailed to fetch"

def get_wikipedia_links():
    MP_LINK = 'http://fi.wikipedia.org/wiki/Luokka:Nykyiset_kansanedustajat'

    print "Populating Wikipedia links to MP's..."
    mp_list = Member.objects.all()
    mp_names = [mp.name for mp in mp_list]
    s = open_url_with_cache(MP_LINK, 'misc')
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
    s = open_url_with_cache(STAT_URL_BASE + STAT_COUNTY_URL, 'county')

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
    mpage = open_url_with_cache(KEYWORD_URL_BASE + KEYWORD_LIST_URL, 'keyword')
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
        kpage = open_url_with_cache(kpage_url, 'keyword')
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
        s = open_url_with_cache(url, link_type, new_only)
        doc = html.fromstring(s)
        votes = doc.xpath(".//div[@class='listing']/div/p")
        doc.make_links_absolute(url)

        for vote in votes:
            link = {}

            elem_list = vote.xpath('.//a')
            links = [l.attrib['href'] for l in elem_list]

            minutes_link = [l for l in links if '/akxptk.sh?' in l]
            if len(minutes_link) != 1:
                print get_cache_fname(url, link_type)
                raise Exception("Unable to find link to minutes")
            link['minutes'] = minutes_link[0]

            if not is_minutes:
                link_list = [l for l in links if '=aax/aax5000&' in l]
                if len(link_list) != 1:
                    raise Exception("Unable to find vote results")
                link['results'] = link_list[0]

                link_list = [l for l in links if '/vex3000.sh?' in l]
                if len(link_list) != 1:
                    print >> sys.stderr, 'Warning: Vote does not have keyword info'
                else:
                    link['info'] = link_list[0]

            ret.append(link)

        # Check if last page of links
        if len(votes) >= 50:
            fwd_link = doc.xpath(".//input[@name='forward']")
            url = url_base + fwd_link[0].attrib['value']
        else:
            fwd_link = None
            break
        if new_only:
            break


    return (ret, fwd_link)

pl_sess_list = {}
mem_name_list = {}

@transaction.commit_manually
def process_session_votes(url, nr, only_new=False, noop=False):
    parser = vote_list_parser.Parser()
    s = open_url_with_cache(url, 'votes')
    parser.reset()
    parser.feed(s)
    parser.close()
    votes = parser.get_votes()
    desc = parser.get_desc()

    sess_id = desc['pl_session']
    if until_pl:
        only_new = False
        if sess_id == until_pl:
            return False
    desc['nr'] = int(desc['nr'])
    print '%4d. Vote %d / %s' % (nr, desc['nr'], desc['pl_session'])

    if noop:
        return True

    deleted_pl = False
    if sess_id in pl_sess_list:
        pl_sess = pl_sess_list[sess_id]
    else:
        try:
            pl_sess = PlenarySession.objects.get(name=sess_id)
        except PlenarySession.DoesNotExist:
            pl_sess = None

        if not pl_sess:
            PlenarySession.objects.filter(name=sess_id).delete()
            deleted_pl = True
            pl_sess = PlenarySession()
            pl_sess.name = sess_id
            pl_sess.date = desc['date']
            pl_sess.info_link = url_base + desc['session_link']
            pl_sess.save()

    pl_sess_list[sess_id] = pl_sess

        # If the plenary session was deleted, all the child
        # objects were, too.

    if not deleted_pl:
        try:
            sess = Session.objects.get(plenary_session=pl_sess,
                    number=desc['nr'])
        except Session.DoesNotExist:
            sess = None
        if only_new and sess:
            return False
        if sess:
            sess.delete()

    sess = Session()
    sess.plenary_session = pl_sess
    sess.number = desc['nr']
    sess.time = desc['time']
    sess.info = '\n'.join(desc['info'])
    sess.subject = desc['subject']
    sess.info_link = None
    sess.save()

    for doc in desc['docs']:
        name = doc[0]
        try:
            sd = SessionDocument.objects.get(name=name)
        except SessionDocument.DoesNotExist:
            sd = SessionDocument(name=name)
        sd.info_link = url_base + doc[1]
        sd.save()
        sd.sessions.add(sess)

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

    transaction.commit()
    db.reset_queries()

    return sess

def process_session_keywords(url, sess, noop=False):
    s = open_url_with_cache(url, 'votes')
    doc = html.fromstring(s)
    kw_list = doc.xpath(".//div[@id='vepsasia-asiasana']//div[@class='linkspace']/a")
    print sess

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

def process_votes(full_update=False, noop=False):
    year = END_YEAR
    next_link = None
    while True:
        if not next_link:
            next_link = url_base + VOTE_URL % year
        (vote_links, next_link) = read_links(False, next_link, not full_update)
        print 'Got links for total of %d sessions' % len(vote_links)
        for link in vote_links:
            nr = vote_links.index(link)
            sess = process_session_votes(link['results'], nr, not full_update, noop)
            if not sess:
                return
            # Process keywords
            if 'info' in link:
                process_session_keywords(link['info'], sess, noop)

        if not next_link:
            year -= 1
            if year < BEGIN_YEAR:
                break

def insert_minutes(full_update, minutes):
    if until_pl and minutes['id'] == until_pl:
        return False
    print minutes['id']
    mins = None
    try:
        pl_sess = PlenarySession.objects.get(name=minutes['id'])

        # If the plsession exists and has the minutes field set
        # already, but we're not doing a full update, bail out.
        mins = Minutes.objects.get(plenary_session=pl_sess)
        if not full_update and mins:
            return None
    except PlenarySession.DoesNotExist:
        pl_sess = PlenarySession()
        pl_sess.name = minutes['id']
        pl_sess.date = minutes['date']
        pl_sess.info_link = minutes['url']
        pl_sess.save()
    except Minutes.DoesNotExist:
        mins = None

    if not mins:
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
                  214, 252, 229, 197, 167, 353, 228, 160, 246]
            if ord(n) >= 128 and ord(n) not in OK:
                print '%d: %c' % (ord(n), n)
                print st.text[st.text.index(n):]
                match = True
        st.html = spkr['html']
        st.save()
    return True


@transaction.commit_manually
def process_minutes(full_update):
    member_list = Member.objects.all()
    member_dict = {}
    for mem in member_list:
        (last, first) = mem.name.split(' ', 1)
        name = ' '.join((first, last))
        if name in member_dict:
            raise Exception()
        member_dict[name] = mem

    next_link = url_base + MINUTES_URL
    while True:
        (links, next_link) = read_links(True, next_link, new_only=not full_update)
        print 'Got links for total of %d minutes' % len(links)
        for link in links:
            url = link['minutes']
            print '%4d. %s' % (links.index(link), url)
            s = open_url_with_cache(url, 'minutes')
            tmp_url = 'http://www.eduskunta.fi/faktatmp/utatmp/akxtmp/'
            minutes = minutes_parser.parse_minutes(s, tmp_url)
            if not minutes:
                continue
            s = open_url_with_cache(minutes['sgml_url'], 'minutes')
            minutes['url'] = url
            pl_sess = insert_minutes(full_update, minutes)
            if not pl_sess:
                next_link = None
                break
            for l in minutes['cnv_links']:
                print l
                s = open_url_with_cache(l, 'minutes')
                disc = minutes_parser.parse_discussion(s, l)
                insert_discussion(full_update, pl_sess, disc,
                                  minutes['cnv_links'].index(l),
                                  member_dict)
            transaction.commit()
            db.reset_queries()
        if not next_link:
            break

parser = OptionParser()
parser.add_option('-p', '--parties', action='store_true', dest='parties'
                  , help='populate party database')
parser.add_option('-m', '--members', action='store_true', dest='members'
                  , help='populate member database')
parser.add_option('-c', '--counties', action='store_true',
                  dest='counties', help='populate counties database')
parser.add_option('-v', '--votes', action='store_true', dest='votes',
                  help='populate vote database')
parser.add_option('-M', '--minutes', action='store_true', dest='minutes'
                  , help='populate session minutes database')
parser.add_option('-k', '--keywords', action='store_true', dest='keywords'
                  , help='populate voting keywords database')
parser.add_option('--cache', action='store', type='string', dest='cache'
                  , help='use cache in directory CACHE')
parser.add_option('--full-update', action='store_true',
                  dest='full_update',
                  help='perform a full database update')
parser.add_option('--until-pl', action='store', type='string',
                  dest='until_pl',
                  help='process until named plenary session reached')

(opts, args) = parser.parse_args()

party_list = None
if opts.cache:
    cache_dir = opts.cache
if opts.until_pl:
    until_pl = opts.until_pl
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
