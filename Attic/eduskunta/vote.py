# -*- coding: utf-8 -*-
import re
import os
from datetime import datetime
from lxml import etree, html
from django import db
from eduskunta.importer import Importer, ParseError
from parliament.models.session import *
from parliament.models.member import Member
from .member import fix_mp_name

VOTE_MAP = {
    'Jaa': 'Y',
    'Ei': 'N',
    'Tyhjää': 'E',
    'Poissa': 'A',
}

PROCESSING_STEP = {
	'Ensimmäinen käsittely': '1H',
	'Toinen käsittely': '2H',
	'Ainoa käsittely': 'OH',
	'Yksi käsittely': 'OH',
	'Ulkopuolella päiväjärjestyksen': 'OA',
	'Osittain ainoa, osittain toinen käsittely': '2H-OH',
	'Toinen käsittely, ainoa käsittely': '2H-OH',
	'Jatkettu ensimmäinen käsittely': '1H',
	'Palautekeskustelu': '??',
	'Lähetekeskustelu': '??',
	'Vaalit': 'EL',
	'Vaaleja': 'EL',
	'Täysistuntokäsittely': 'PV',
	'Ilmoituksia': '??',
	'Kolmas käsittely': '??',
}

def parse_vote(mp, vote):
    (name, party) = mp.split('/')
    name = name.strip()
    party = party.strip()
    v = VOTE_MAP[vote]
    if 'puhemiehe' in party:
        v = 'S'
        party = party.split()[0]
    name = fix_mp_name(name)

    return {'name': name, 'party': party, 'vote': v}

class VoteImporter(Importer):
    VOTE_URL = '/triphome/bin/thw.cgi/trip/?${html}=aax/aax4000&${base}=aanestysu&aanestysvpvuosi=%d&istuntonro=%s&aanestysnro=%d'
    VOTE_LIST_URL = '/triphome/bin/aax3000.sh?VAPAAHAKU=aanestysvpvuosi=%i'
    BEGIN_YEAR = 1999
    CACHE_DIR = 'votes'

    def save_session(self, pv, info):
        dt = datetime.strptime('%s %s' % (str(pv.plsess.date), info['time']),
                               '%Y-%m-%d %H.%M')
        pv.time = dt
        assert pv.time.date() == pv.plsess.date, 'Vote %s time mismatch (%s vs. %s)' % (pv, pv.time, pv.plsess)
        pv.setting = info['setting']
        pv.subject = info['subject']
        pv.save()
        Vote.objects.filter(session=pv).delete()
        for vi in info['votes']:
            mp = self.mp_by_name[vi['name']]
            if vi['vote'] == 'S':
                continue
            vote = Vote(session=pv, vote=vi['vote'], member=mp, party=vi['party'])
            vote.save()
        pv.count_votes()
        counts = [int(v) for v in pv.vote_counts.split(',')]
        n = 0
        for v in counts:
            n += v
        assert n in (197, 198, 199)
        pv.save()
        return pv

    def import_session(self, info):
        if not info['plsess'] in self.plsess_by_id:
            try:
                plsess = PlenarySession.objects.get(origin_id=info['plsess'])
            except PlenarySession.DoesNotExist:
                raise Exception("Vote %s refers to unexisting plenary session" % (info['number'], info['plsess']))
            self.plsess_by_id[info['plsess']] = plsess

        plsess = self.plsess_by_id[info['plsess']]
        try:
            pv = PlenaryVote.objects.get(plsess=plsess, number=info['number'])
            if not self.replace:
                return
        except PlenaryVote.DoesNotExist:
            pv = PlenaryVote(plsess=plsess, number=info['number'])

        self.logger.info('processing plenary vote %s/%d' % (plsess.name, info['number']))
        s = self.open_url(info['link'], self.CACHE_DIR)

        doc = html.fromstring(s)

        hdr_el = doc.xpath('//table[@class="voteResults"]')
        if len(hdr_el) < 1:
            raise ParseError('vote header not found')
        hdr_el = hdr_el[0]
        s = self.clean_text(hdr_el.xpath('caption')[0].text)
        m = re.match(r'Äänestys (\d+) klo (\d{2}\.\d{2})', s, re.U)
        info['time'] = m.groups()[1]

        el = hdr_el.xpath('tbody/tr')[0].xpath('td')[1]
        s = self.clean_text(el.text)
        info['subject'] = s

        el = hdr_el.xpath('tbody/tr/td/strong')[0]
        s = self.clean_text(el.text)
        step = PROCESSING_STEP[s]

        el = doc.xpath("//th[contains(., 'nestysasettelu')]")[0]
        s = self.clean_text(el.getnext().text)
        info['setting'] = s

        vote_list_el = doc.xpath('//table[@class="statistics"]/tbody/tr')
        if len(vote_list_el) < 196/2 or len(vote_list_el) > 200/2:
            raise ParseError('vote list not found')
        votes = []
        for row_el in vote_list_el:
            td_list = row_el.xpath('td')
            if len(td_list) != 5:
                raise ParseError('invalid vote row')
            votes.append(parse_vote(td_list[0].text, td_list[1].text))
            if td_list[3].text:
                votes.append(parse_vote(td_list[3].text, td_list[4].text))
        info['votes'] = votes

        pv.mark_modified()
        pv.mark_checked()

        self.updated += 1

        return self.save_session(pv, info)

    def _make_obj_lists(self):
        if not hasattr(self, 'mp_by_name'):
            mp_list = Member.objects.all()
            mpd = {}
            for mp in mp_list:
                mpd[mp.name] = mp
            self.mp_by_name = mpd

        if not hasattr(self, 'plsess_by_id'):
            plsess_list = PlenarySession.objects.all()
            psd = {}
            for pl in plsess_list:
                psd[pl.origin_id] = pl
            self.plsess_by_id = psd

    def _import_one(self, vote_id):
        (year, plsess, nr) = vote_id.split('/')
        url = self.URL_BASE + self.VOTE_URL % (int(year), plsess, int(nr))
        el_list, next_link = self.read_listing(self.CACHE_DIR, url)
        if len(el_list) != 1:
            raise ParseError("vote with id %s not found" % vote_id, url=url)
        el = el_list[0]
        vote_id_str = "%s/%s/%s" % (plsess, year, nr)
        got_id = "%s/%d" % (el['plsess'], el['number'])
        if vote_id_str != got_id:
            raise ParseError("invalid vote returned (wanted %s, got %s)" % (vote_id_str, got_id), url=url)
        info = {'plsess': el['plsess'], 'number': el['number']}
        info['link'] = el['results_link']
        try:
            plv = self.import_session(info)
        except ParseError as e:
            e.url = url
            raise
        db.reset_queries()
        return plv

    def import_one(self, vote_id):
        self._make_obj_lists()
        self.updated = 0

        try:
            plv = self._import_one(vote_id)
        except ParseError as e:
            if e.url:
                # nuke the cache if we have one
                fname = self.http.get_fname(e.url, self.CACHE_DIR)
                if fname:
                    os.unlink(fname)
            self.logger.error("exception: %s" % e)
            # retry
            plv = self._import_one(vote_id)
        return plv

    def import_votes(self, **options):
        self._make_obj_lists()
        self.full_update = options.get('full')
        self.updated = 0
        if options.get('single', False):
            self.replace = True

        this_year = datetime.now().year
        for year in range(this_year, self.BEGIN_YEAR-1, -1):
            next_link = self.URL_BASE + self.VOTE_LIST_URL % year

            year_votes = PlenaryVote.objects.filter(plsess__name__endswith=year)
            seen_votes = []
            while next_link:
                updated_begin = self.updated
                self.logger.debug("Fetching from %s" % next_link)
                el_list, next_link = self.read_listing(self.CACHE_DIR, next_link)
                for el in el_list:
                    if el['plsess'] == '85/1999':
                        # First plenary session in origin database
                        next_link = None
                        break
                    vote_id = '%s/%s' % (el['number'], el['plsess'])
                    seen_votes.append(vote_id)
                    info = {'plsess': el['plsess'], 'number': el['number']}
                    info['link'] = el['results_link']
                    if 'single' in options:
                        if options['single'] != vote_id:
                            continue
                    self.import_session(info)
                    db.reset_queries()
                    if options.get('single', None) == vote_id:
                        return

                updated_this_round = self.updated - updated_begin
                if not updated_this_round and not self.full_update and not options.get('single', None):
                    return

            if not options.get('single', None):
                for plvote in list(year_votes):
                    vote_id = '%d/%s' % (plvote.number, plvote.plsess.name)
                    if vote_id not in seen_votes:
                        print(("Vote %s not found anymore" % vote_id))
                        plvote.delete()
