# -*- coding: utf-8 -*-
import re
import os
import logging
import difflib
from lxml import etree, html
from django.conf import settings
from parliament.models.member import *
from parliament.models.party import Party
from eduskunta.importer import Importer, ParseError
from eduskunta.party import pg_to_party

MEMBER_NAME_TRANSFORMS = {
    'Korhonen Timo': 'Korhonen Timo V.',
    'Ollila Heikki': 'Ollila Heikki A.',
    'Saarela Tanja': 'Karpela Tanja',
    'Kumpula Miapetra': 'Kumpula-Natri Miapetra',
    'Forsius-Harkimo Merikukka': 'Forsius Merikukka',
    'Taberman Tommy': 'Tabermann Tommy',
    'Harkimo Leena-Kaisa': 'Harkimo Leena',
    'Packalen Tom': 'Packalén Tom',
    'Virtanen Pertti "Veltto"': 'Virtanen Pertti',
    'Elomaa Kike': 'Elomaa Ritva',
    'Maijala Eeva-Maria': 'Maijala Eeva Maria',
    'Gästgivars Lars': 'Gästgivars Lars Erik',
    'Gästgivars Lars-Erik': 'Gästgivars Lars Erik',
    # funding 2011
    'Modig Anna': 'Modig Silvia',
    'Wallinheimo Mika': 'Wallinheimo Sinuhe',
    'Huovinen Krista': 'Huovinen Susanna',
    'Stubb Cai-Göran': 'Stubb Alexander',
    'Anttila Sirkka': 'Anttila Sirkka-Liisa',
    'Viitanen Pia-Liisa': 'Viitanen Pia',
    'Vikman Maria': 'Vikman Sofia',
    'Väätäinen Toivo': 'Väätäinen Juha',
    'Pekkarinen Reijo': 'Pekkarinen Mauri',
    'Koskinen Hannu': 'Koskinen Johannes',
    'Jungner Juhani': 'Jungner Mikael',
    'Wideroos Cecilia': 'Wideroos Ulla-Maj',
    'Maijala Eeva': 'Maijala Eeva Maria',
    'Nauclér Charlotte': 'Nauclér Elisabeth',
    'Kiljunen Leila': 'Kiljunen Anneli',
    'Joutsenlahti Juha': 'Joutsenlahti Anssi',
    'Gestrin Anna': 'Gestrin Christina',
    'Mäkinen Heikki': 'Mäkinen Tapani',
    'Jääskeläinen Osmo': 'Jääskeläinen Pietari',
    'Viitamies Johanna': 'Viitamies Pauliina',
    'Kerola Eeva': 'Kerola Inkeri',
    'Orpo Antti': 'Orpo Petteri',
    'Hiltunen Lea': 'Hiltunen Rakel',
    'Tolppanen Eeva': 'Tolppanen Maria',
    'Maijala Eeva Maria': 'Maijala Eeva-Maria',
    'Saarikko Annikka': 'Saarikko Annika',
    'Moilanen-Savolainen Riikka': 'Moilanen Riikka',
    'Mönkäre Sinikka': 'Laisaari Sinikka',
    'Karttunen-Raiskio Marjukka': 'Karttunen Marjukka',
}


def fix_mp_name(name):
    if not isinstance(name, unicode):
        name = name.decode('utf8')
    if name.encode('utf8') in MEMBER_NAME_TRANSFORMS:
        name = MEMBER_NAME_TRANSFORMS[name.encode('utf8')].decode('utf8')
    return name


FIELD_MAP = {
    'name': u'Täydellinen nimi',
    'phone': u'Puhelin',
    'email': u'Sähköposti',
    'occupation': u'Ammatti / Arvo',
    'birth': u'Syntymäaika ja -paikka',
    'home_county': u'Nykyinen kotikunta',
    'districts': u'Vaalipiiri',
    'parties': u'Eduskuntaryhmät',
    'current_posts': u'Nykyiset toimielinjäsenyydet ja tehtävät',
    'previous_posts': u'Aiemmat jäsenyydet ja tehtävät eduskunnan toimielimissä',
    'parliament_groups': u'Eduskuntaryhmät',
    'parliament_group_tasks': u'Tehtävät eduskuntaryhmässä'
}


def get_field_el(doc, field):
    # Get "doclist-items" elements listed by table headers (th)  
    el_list = doc.xpath('//div[@class="doclist-items"]/div[@class="listborder"]/table//th')
    for el in el_list:
        s = el.text.split(':')[0].strip()
        if s == FIELD_MAP[field]:
            # td follows th, so positional selection can be used
            td = el.getnext()
            if td.tag != 'td':
                raise ParseError('expecting a td element')
            return td
    return None

# FIXME: should this be a method of MemberImporter?
    
def parse_membership(line):
    def parse_date(s, is_begin):
        # Filter 'I' and 'II'
        s = s.strip('I ')
        DATE_MATCH = r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$'
        m = re.match(DATE_MATCH, s)
        if not m:
            m = re.match(r'^(\d{4})$', s)
            if not m: 
                return None
            if is_begin:
                day, mon = 1, 1
            else:
                day, mon = 31, 12
            year = int(m.groups()[0])
        else:
            day, mon, year = [int(x) for x in m.groups()]
        return '-'.join([str(x) for x in (year, mon, day)])

    info = {}
    m = re.match(r'([^0-9(]+)(.+)', line)
    assert m, "Committee name not found: %s" % line
    committee_name = m.groups()[0].strip()
    # Only record committees (valiokunta)
    if committee_name.endswith('valiokunta'):
        info['committee'] = committee_name
        date_line = m.groups()[1].strip()
        # Check if there are historical committee names in the string.
        m = re.match(r'\([^)]+\d+[^)]+\) ', date_line)
        if m is not None:
            # If match found, strip the historical names.
            date_line = date_line[date_line.find(')') + 1:].strip()
        membership_dates = []
        for m_line in date_line.split(','):
            d = {}
            m_line = m_line.strip()
            m = re.match(r'\((\w+)\) ([0-9. I-]+)', m_line)
            if m:
                d['role'] = m.groups()[0]
                m_line = m.groups()[1]
            dates = m_line.split(' -')
            d['begin'] = parse_date(dates[0], True)
            if len(dates) > 1 and len(dates[1]):
                d['end'] = parse_date(dates[1].strip(), False)
            else:
                d['end'] = None
            # Exclude cases where both begin and end are None
            if not d['begin'] and not d['end']:
                continue
            else:
                membership_dates.append(d)
        info['periods'] = membership_dates
        return info
    else:
        return None

class MemberImporter(Importer):
    LIST_URL = '/triphome/bin/thw/trip/?${base}=hetekaue&${maxpage}=10001&${snhtml}=hex/hxnosynk&${html}=hex/hx4600&${oohtml}=hex/hx4600&${sort}=lajitnimi&nykyinen=$+and+(VPR_LOPPUTEPVM+%3E=24.03.1999)'
    MP_INFO_URL = '/triphome/bin/hex5000.sh?hnro=%d&kieli=su'
    DATE_MATCH = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
    DISTRICTS_FILE = 'districts.txt'

    def import_districts(self):
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, self.DISTRICTS_FILE))
        for line in f.readlines():
            line = line.strip().decode('utf8')
            if not line or line[0] == '#':
                continue
            m = re.match(r'(\d+)\s+([\w \-]+)$', line, re.U)
            nr = m.groups()[0]
            district = m.groups()[1]
            try:
                d = District.objects.get(name=district)
                if not self.replace:
                    continue
            except District.DoesNotExist:
                self.logger.debug("creating district '%s'" % district)
                d = District(name=district)
            d.long_name = "%s vaalipiiri" % district
            d.save()

    def fetch_member(self, mp_id):
        url = self.URL_BASE + self.MP_INFO_URL % mp_id
        s = self.open_url(url, 'member')
        doc = html.fromstring(s)
        doc.make_links_absolute(url)

        mp_info = {'id': mp_id, 'info_url': url}

        name_el = doc.xpath('//div[@id="content"]/div[@class="header"]/h1')
        if len(name_el) != 1:
            raise ParseError("MP name not found")
        name, pg = name_el[0].text.strip().split('/')
        name = name.strip()
        pg = pg.strip()
        names = name.split()
        surname, first_names = names[-1], ' '.join(names[0:-1])
        mp_info['name'] = "%s %s" % (surname, first_names)

        surname, given_names = get_field_el(doc, 'name').text.strip().split(', ')
        if '(' in given_names:
            given_names = given_names.split('(')[0].strip()
        mp_info['surname'] = surname
        mp_info['given_names'] = given_names.strip()

        td = get_field_el(doc, 'phone')
        if td is not None:
            mp_info['phone'] = td.text.strip()

        td = get_field_el(doc, 'email')
        if td is not None:
            mp_info['email'] = td.text_content().strip().replace('[at]', '@')

        td = get_field_el(doc, 'birth')
        text = td.text.strip()
        # First try to match the birthplace, too
        m = re.match(self.DATE_MATCH + r'\s+(\w+)', text, re.U)
        if not m:
            m = re.match(self.DATE_MATCH, text, re.U)
            if not m:
                raise ParseError("Invalid MP birth date")
        (day, mon, year) = m.groups()[0:3]
        mp_info['birthdate'] = '-'.join((year, mon, day))
        if len(m.groups()) == 4:
            mp_info['birthplace'] = m.groups()[3]

        # Electorate

        td = get_field_el(doc, 'home_county')
        if td is not None:
            mp_info['home_county'] = td.text.strip()

        td = get_field_el(doc, 'districts')
        el_list = td.xpath('ul/li')
        da_list = []
        for el in el_list:
            district, date_range = el.text.strip().split('  ')
            dates = date_range.split(' - ')
            da = {'district': district, 'begin': self.convert_date(dates[0])}
            if len(dates) > 1:
                da['end'] = self.convert_date(dates[1])
            da_list.append(da)
        mp_info['districts'] = da_list 

        # Party memberships

        td = get_field_el(doc, 'parties')
        el_list = td.xpath('ul/li')
        pa_list = []
        for el in el_list:
            a_el = el.xpath('a')
            if not a_el:
                # Strip text within parentheses
                m = re.match(r'([^\(]*)\([^\),]+\)(.+)', el.text)
                if m:
                    text = ' '.join(m.groups())
                else:
                    text = el.text
                m = re.match(r'(\D+)\s+([\d\.,\s\-]+)$', text.strip())
                party, date_ranges = (m.groups()[0], m.groups()[1])
            if not a_el:
                # Strip text within parentheses
                m = re.match(r'([^\(]*)\([^\),]+\)(.+)', el.text)
                if m:
                    text = ' '.join(m.groups())
                else:
                    text = el.text
                m = re.match(r'(\D+)\s+([\d\.,\s\-]+)$', text.strip())
                party, date_ranges = (m.groups()[0], m.groups()[1])
            else:
                a_el = a_el[0]
                party, date_ranges = (a_el.text.strip(), a_el.tail.strip())

            # Strip text within parentheses
            m = re.match(r'([^\(]*)\([^\)]+\)(.+)', date_ranges)
            if m:
                date_ranges = ' '.join(m.groups())

            for dr in date_ranges.split(','):
                pa = {'party': party}
                dates = dr.strip().split(' - ')
                pa['begin'] = self.convert_date(dates[0])
                if len(dates) > 1:
                    pa['end'] = self.convert_date(dates[1])
                pa_list.append(pa)
        mp_info['parties'] = pa_list

        img_el = doc.xpath('//div[@id="submenu"]//img[@class="portrait"]')
        mp_info['portrait'] = img_el[0].attrib['src']

        # Committee memberships
        mp_info['posts'] = self.resolve_memberships(doc)

        return mp_info

    def determine_party(self, mp_info):
        pa_list = mp_info['parties']
        latest_pa = pa_list[0]
        for pa in pa_list[1:]:
            if pa['begin'] > latest_pa['begin']:
                if not pg_to_party(pa['party']):
                    continue
                latest_pa = pa
        party_name = pg_to_party(latest_pa['party'])
        if party_name:
            party = Party.objects.get(name=party_name)
            return party
        return None

    def save_member(self, mp_info):
        # Member
        try:
            mp = Member.objects.get(origin_id=str(mp_info['id']))
            if not self.replace:
                return
        except Member.DoesNotExist:
            mp = Member(origin_id=str(mp_info['id']))
        mp.name = mp_info['name']
        mp.birth_date = mp_info['birthdate']
        if 'birthplace' in mp_info:
            mp.birth_place = mp_info['birthplace']
        mp.given_names = mp_info['given_names']
        mp.surname = mp_info['surname']
        if 'email' in mp_info:
            mp.email = mp_info['email']
        else:
            mp.email = None
        if 'phone' in mp_info:
            mp.phone = mp_info['phone']
        else:
            mp.phone = None
        mp.info_link = mp_info['info_url']
        mp.party = self.determine_party(mp_info)

        url = mp_info['portrait']
        ext = url.split('.')[-1]
        fname = slugify(mp.name) + '.' + ext
        dir_name = os.path.join(mp.photo.field.upload_to, fname)
        path = os.path.join(settings.MEDIA_ROOT, dir_name)
        mp.photo = dir_name
        if not os.path.exists(path):
            self.logger.debug("getting MP portrait")
            s = self.open_url(url, 'members')
            f = open(path, 'wb')
            f.write(s)
            f.close()

        mp.save()

        # Districts
        DistrictAssociation.objects.filter(member=mp).delete()
        for da in mp_info['districts']:
            d_name = da['district'].replace(' vaalipiiri', '')
            try:
                district = District.objects.get(long_name=da['district'])
            except District.DoesNotExist:
                district = None
            da_obj = DistrictAssociation(member=mp, begin=da['begin'])
            da_obj.district = district
            da_obj.name = d_name
            if 'end' in da:
                da_obj.end = da['end']
            da_obj.save()

        # Parties
        PartyAssociation.objects.filter(member=mp).delete()
        for pa in mp_info['parties']:
            p_name = pg_to_party(pa['party'])
            if p_name:
                party = Party.objects.get(name=p_name)
            else:
                party = None
            pa_obj = PartyAssociation(member=mp, begin=pa['begin'])
            pa_obj.party = party
            pa_obj.name = pa['party']
            if 'end' in pa:
                pa_obj.end = pa['end']
            pa_obj.save()

        # Memberships

        if mp_info['posts'] is not None:
            for post in mp_info['posts']:
                try:
                    committee = Committee.objects.get(name=post['committee'])
                    # Update current committees
                    if committee.current == False and post['current'] == True:
                        committee.current = True
                        committee.save()
                except Committee.DoesNotExist:
                    committee = Committee(name=post['committee'],
                                          current=post['current'])
                    committee.save()
                # Delete all the associations already in the db
                CommitteeAssociation.objects.filter(member=mp,
                    committee_id = committee.id).delete()
                # There can be several periods
                periods = post['periods']
                for period in periods:
                    # Role is only optional information
                    if 'role' in period:
                        role = period['role']
                    else:
                        role = None
                    ca_obj = CommitteeAssociation(member=mp, committee=committee, 
                                                  begin=period['begin'], end=period['end'], 
                                                  role=role)
                    ca_obj.save()

    def resolve_memberships(self, doc):
        membership_list = []
        for period in ['previous_posts', 'current_posts']:
            td = get_field_el(doc, period)
            if td is not None:
                el_list = td.xpath('ul/li')
                for el in el_list:
                    a_el = el.xpath('a')
                    if a_el:
                        try:
                            membership_desc = a_el[0].text + a_el[0].tail
                        except TypeError, e:
                            self.logger.warning("Problem parsing item")
                            self.logger.warning(html.tostring(el))
                    else:
                        membership_desc = el.text
                    ms = parse_membership(membership_desc)
                    if ms is not None:
                        if period == 'previous_posts':
                            ms['current'] = False
                        elif period == 'current_posts':
                            ms['current'] = True
                        membership_list.append(ms)
                    else:
                        continue
        return membership_list

    def get_wikipedia_links(self):
        MP_LINK = 'http://fi.wikipedia.org/wiki/Luokka:Nykyiset_kansanedustajat'

        print "Populating Wikipedia links to current MPs..."
        mp_list = list(Member.objects.current())
        mp_names = [mp.name for mp in mp_list]
        s = self.http.open_url(MP_LINK, 'wikipedia')
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
            for mp in mp_list:
                if mp.name == name:
                    break
            else:
                matches = difflib.get_close_matches(name, mp_names, cutoff=0.8)
                if len(matches) > 1:
                    raise Exception("Multiple matches for '%s'" % name)
                elif not matches:
                    print "No match found for '%s'" % name
                    continue
                print("Mapping '%s' to %s'" % (name, matches[0]))
                for mp in mp_list:
                    if mp.name == matches[0]:
                        break
                else:
                    raise Exception("MP %s not found" % matches[0])
            mp.wikipedia_link = href
            mp.found = True
            #get_mp_homepage_link(mp)
            mp.save()
        for mp in mp_list:
            if not hasattr(mp, 'found'):
                print "%s not found" % mp

    def import_members(self):
        self.logger.debug("fetching MP list")
        list_url = self.URL_BASE + self.LIST_URL
        s = self.open_url(list_url, 'member')
        doc = html.fromstring(s)
        doc.make_links_absolute(list_url)
        link_list = doc.xpath("//a[@target='edus_main']")
        for l in link_list:
            name = l.text.strip().replace('&nbsp', '')
            url = l.attrib['href']
            self.logger.debug("fetching MP %s" % name)
            s = self.open_url(url, 'member')
            doc = html.fromstring(s)
            el = doc.xpath("//frame[@name='vasen2']")
            if len(el) != 1:
                raise ParseError("Invalid MP info frame")
            s = el[0].attrib['src']
            m = re.search(r'hnro=(\d+)', s)
            if not m:
                raise ParseError("MP ID not found")
            mp_id = int(m.groups()[0])

            mp_info = self.fetch_member(mp_id)
            self.save_member(mp_info)
        self.logger.info('Imported {0} MPs'.format(len(link_list)))
