#!/usr/bin/python

import urllib2
import cookielib
import time
import sys
import os
import re
import sqlite3
import hashlib
import operator
from optparse import OptionParser

import session_list_parser
import vote_list_parser
import mop_list_parser
import mop_info_parser
import party_list_parser
import party_info_parser
import minutes_parser

from django.core.management import setup_environ

my_path = os.path.dirname(__file__)
app_base = my_path + '/../'

sys.path.append(my_path + '/../..')
sys.path.append(my_path + '/..')

from kamu import settings
setup_environ(settings)
from django.db import connection, transaction
from django import db

import kamu.votes.models
from kamu.votes.models import *

cache_dir = None
until_pl = None

def create_path_for_file(fname):
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
                os.makedirs(dirname)

def open_url_with_cache(url, prefix, skip_cache = False):
        fname = None
        if cache_dir and not skip_cache:
                fname = cache_dir + '/' + prefix + '/' + url.replace("/", "-")
        if not fname or not os.access(fname, os.R_OK):
                opener = urllib2.build_opener(urllib2.HTTPHandler)
                f = opener.open(url)
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

url_base = "http://www.eduskunta.fi"
mp_photo_path = 'images/members/'
party_logo_path = 'images/parties/'

party_url_base = "http://web.eduskunta.fi"
party_list_url = "/Resource.phx/eduskunta/organisaatio/kansanedustajat/kansanedustajateduskuntaryhmittain.htx"

mp_list_url = "/triphome/bin/thw/trip/?${base}=hetekaue&${maxpage}=10001&${snhtml}=hex/hxnosynk&${html}=hex/hx4600&${oohtml}=hex/hx4600&${sort}=lajitnimi&nykyinen="\
        "$+and+vpr_alkutepvm%3E=22.03.1991"
heti_url = "/triphome/bin/hex5000.sh?hnro=%s&kieli=su"

STAT_URL_BASE = "http://www.stat.fi"
STAT_COUNTY_URL = "/meta/luokitukset/vaalipiiri/001-2007/luokitusavain_teksti.txt"

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
                        print "Fetching logo " + logo_url
                        s = open_url_with_cache(logo_url, 'party')
                        f = open(fname, 'wb')
                        f.write(s)
                        f.close()
                else:
                        print "Skipping logo " + party['logo']

                if not db_insert:
                        continue

                try:
                        p = Party.objects.get(name = party['name'])
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

def process_mops(party_list, update = False, db_insert = False):
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
                print "%3d: %s, %s" % (mop_list.index(mp), mp['surname'], mp['firstnames'])
                s = open_url_with_cache(url_base + mp['link'], 'member')
                parser.reset(is_lame_frame = True)
                parser.feed(s)
                parser.close()
                mp.update(parser.get_desc())

                print "%3d: person number %s" % (mop_list.index(mp), mp['hnro'])

                try:
                        member = Member.objects.get(pk = mp['hnro'])
                except Member.DoesNotExist:
                        member = None

                if member and not update:
                        continue

                s = open_url_with_cache(url_base + (heti_url % mp['hnro']), 'member')
                parser.reset(is_lame_frame = False)
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
                        print "Fetching photo " + photo_url
                        s = open_url_with_cache(photo_url, 'member')
                        f = open(photo_fname, 'wb')
                        f.write(s)
                        f.close()
                else:
                        print "Skipping photo " + mp['photo']

                party_name = None
                if 'party' in mp:
                        party_name = find_party(party_list, mp['party'])
                        if not party_name:
                                raise Exception("Unknown party")

                for assoc in mp['assoc']:
                        if 'end' not in assoc:
                                end = None
                        else:
                                end = assoc['end']
                        party = find_party(party_list, assoc['name'])
                        if party == None:
                                if not end:
                                        print assoc
                                        raise Exception("party not found")
                                # FIXME: Maybe add the party?
                                assoc['name'] = None
                        else:
                                assoc['name'] = party

                is_active = False
                # Find last party association
                last_assoc = sorted(mp['assoc'], key=operator.itemgetter('start'))[-1]
                if 'end' not in last_assoc:
                        is_active = True
                else:
                        if party_name:
                                raise Exception("party set for inactive MP")
                        party_name = last_assoc['name']

                if not db_insert:
                        continue

                if not member:
                        member = Member()
                        member.id = mp['hnro']
                member.name = mp['name']
                member.party_id = party_name
                member.photo = mp_photo_path + mp['photo']
                member.info_link = url_base + mp['info_link']
                member.is_active = is_active
                member.birth_date = mp['birthdate']
                member.given_names = mp['firstnames']
                member.surname = mp['surname']
                if 'phone' in mp:
                        member.phone = mp['phone']
                if 'email' in mp:
                        member.email = mp['email']
                member.save()

                PartyAssociation.objects.filter(member = member).delete()
                for assoc in mp['assoc']:
                        if not assoc['name']:
                                continue
                        if 'end' not in assoc:
                                end = None
                        else:
                                end = assoc['end']
                        party = Party.objects.get(name = assoc['name'])
                        pa = PartyAssociation()
                        pa.member = member
                        pa.party_id = party.pk
                        pa.begin = assoc['start']
                        pa.end = end
                        pa.save()
                DistrictAssociation.objects.filter(member = member).delete()
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

def process_counties(db_insert):
        s = open_url_with_cache(STAT_URL_BASE + STAT_COUNTY_URL, 'county')
        # strip first 4 lines of header and any blank/empty lines at EOF
        for line in s.rstrip().split("\n")[4:]:
                dec_line = line.decode("iso8859-1").rstrip().split("\t")
                (district_id, district_name, county_id, county_name) = dec_line

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

#VOTE_URL = "/triphome/bin/aax3000.sh?kanta=&PALUUHAKU=%2Fthwfakta%2Faanestys%2Faax%2Faax.htm&" +\
#           "haku=suppea&VAPAAHAKU=&OTSIKKO=&ISTUNTO=&AANVPVUOSI=(2007%2Bor%2B2008%2Bor%2B2009%2Bor%2B2010)&PVM1=&PVM2=&TUNNISTE="

#VOTE_URL = "/triphome/bin/aax3000.sh?kanta=&PALUUHAKU=%2Fthwfakta%2Faanestys%2Faax%2Faax.htm&" +\
#           "haku=suppea&VAPAAHAKU=&OTSIKKO=&ISTUNTO=&AANVPVUOSI=(2003%2Bor%2B2004%2Bor%2B2005%2Bor%2B2006)&PVM1=&PVM2=&TUNNISTE="
VOTE_URL = "/triphome/bin/aax3000.sh?VAPAAHAKU=aanestysvpvuosi>=1999"
MINUTES_URL = "/triphome/bin/akx3000.sh?kanta=utaptk&uusimmat=k&lajittelu=PAIVAMAARA+desc,tstamp+desc&VAPAAHAKU2=vpvuosi%3E2002&paluuhaku=/triphome/bin/akxhaku.sh%3Flyh=PTKSUP%3Flomake=akirjat/akx3100&haku=PTKSUP"

def read_links(is_minutes, link=None, new_only=False):
        if is_minutes:
                link_type = 'minutes'
                url = MINUTES_URL
        else:
                link_type = 'votes'
                url = VOTE_URL

        links = []
        if cache_dir and not new_only:
                cache_file = cache_dir + '/%s_links.txt' % link_type
                if os.access(cache_file, os.R_OK):
                        f = open(cache_file, 'r')
                        for line in f.readlines():
                                links.append(line.strip())
                        return (links, None)

        parser = session_list_parser.Parser()
        if link:
                url = url_base + link
        else:
                url = url_base + url

        while True:
                s = open_url_with_cache(url, link_type, new_only)
                parser.reset(is_minutes)
                parser.feed(s)
                parser.close()
                l = parser.get_links()
                if not l:
                        return None
                print "Got %d links" % len(l)
                links += l
                # Check if last page of links
                if len(l) >= 50:
                        fwd_link = parser.get_forward_link()
                        url = url_base + fwd_link
                else:
                        fwd_link = None
                        break
                if new_only:
                        break

        if cache_dir and not new_only:
                f = open(cache_file, 'w')
                for link in links:
                        f.write(link + "\n")
                f.close()

        return (links, fwd_link)

pl_sess_list = {}
mem_name_list = {}

@transaction.commit_manually
def process_session_votes(link, nr, only_new=False, noop=False):
        parser = vote_list_parser.Parser()
        url = url_base + link
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
        print "%4d. Vote %d / %s" % (nr, desc['nr'], desc['pl_session'])

        if noop:
                return True

        deleted_pl = False
        if sess_id in pl_sess_list:
                pl_sess = pl_sess_list[sess_id]
        else:
                try:
                        pl_sess = PlenarySession.objects.get(name = sess_id)
                except PlenarySession.DoesNotExist:
                        pl_sess = None

                if not pl_sess:
                        PlenarySession.objects.filter(name = sess_id).delete()
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
                        sess = Session.objects.get(plenary_session = pl_sess, number = desc['nr'])
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
                        sd = SessionDocument.objects.get(name = name)
                except SessionDocument.DoesNotExist:
                        sd = SessionDocument(name = name)
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
#                       print vote.member_id
                        member = Member.objects.get(name = vote.member_name)
                        mem_name_list[vote.member_name] = member
                vote.member = mem_name_list[vote.member_name]
                vote.save()
        sess.count_votes()

        transaction.commit()
        db.reset_queries()

        return True

def process_votes(full_update=False, noop=False):
        next_link = None
        while True:
                (vote_links, next_link) = read_links(False, next_link, not full_update)
                print "Got links for total of %d sessions" % len(vote_links)
                for link in vote_links:
                        nr = vote_links.index(link)
                        if not process_session_votes(link, nr, not full_update, noop):
                                next_link = None
                                break
                if not next_link:
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
                minutes = Minutes.objects.get(plenary_session=pl_sess)
                if not full_update and minutes:
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

OK_UNKNOWNS = [ 'Alexander Stubb', u'Petri J\u00e4\u00e4skel\u00e4inen',
        'Jaakko Jonkka', 'Riitta-Leena Paunio' ]

def insert_discussion(full_update, pl_sess, disc, dsc_nr, members):
        idx = 0
        for spkr in disc:
                if not spkr['name'] in members:
                        if not spkr['name'] in OK_UNKNOWNS:
                                print spkr['name']
                                raise Exception("Unknown member: " + spkr['name'])
                        member = None
                else:
                        member = members[spkr['name']]
                idx = disc.index(spkr)
                try:
                        st = Statement.objects.get(plenary_session = pl_sess,
                                dsc_number = dsc_nr, index = idx)
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
                        OK=[ 225, 224, 189, 232, 237, 352, 248, 201, 180, 233, 196, 214, 252, 229, 197, 167, 353, 228, 160, 246 ]
                        if ord(n) >= 128 and ord(n) not in OK:
                                print "%d: %c" % (ord(n), n)
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

        next_link = None
        while True:
                (links, next_link) = read_links(True, next_link, new_only=not full_update)
                print "Got links for total of %d minutes" % len(links)
                for link in links:
                        url = url_base + link
                        print "%4d. %s" % (links.index(link), url)
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
                                        minutes['cnv_links'].index(l), member_dict)
                        transaction.commit()
                        db.reset_queries()
                if not next_link:
                        break

parser = OptionParser()
parser.add_option('-p', '--parties', action="store_true", dest="parties",
                  help="populate party database")
parser.add_option('-m', '--members', action="store_true", dest="members",
                  help="populate member database")
parser.add_option('-c', '--counties', action="store_true", dest="counties",
                  help="populate counties database")
parser.add_option('-v', '--votes', action="store_true", dest="votes",
                  help="populate vote database")
parser.add_option('-M', '--minutes', action="store_true", dest="minutes",
                  help="populate session minutes database")
parser.add_option('--cache', action="store", type="string", dest="cache",
                  help="use cache in directory CACHE")
parser.add_option('--full-update', action="store_true", dest="full_update",
                  help="perform a full database update")
parser.add_option('--until-pl', action="store", type="string", dest="until_pl",
                  help="process until named plenary session reached")

(opts, args) = parser.parse_args()

party_list = None
if opts.cache:
        cache_dir = opts.cache
if opts.until_pl:
        until_pl = opts.until_pl
if opts.parties or opts.members:
        party_list = process_parties(True)
if opts.members:
        mp_list = process_mops(party_list, True, True)
if opts.counties:
        counties = process_counties(True)
if opts.votes:
        process_votes(opts.full_update)
if opts.minutes:
        process_minutes(opts.full_update)
