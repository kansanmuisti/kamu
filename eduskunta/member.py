# -*- coding: utf-8 -*-
import re
import os
import logging
from lxml import etree, html
from parliament.models.member import Member
from eduskunta.importer import Importer, ParseError
from eduskunta.party import pg_to_party

FIELD_MAP = {
    'name': u'Täydellinen nimi',
    'phone': u'Puhelin',
    'email': u'Sähköposti',
    'occupation': u'Ammatti / Arvo',
    'birth': u'Syntymäaika ja -paikka',
    'home_county': u'Nykyinen kotikunta',
    'districts': u'Vaalipiiri',
    'parties': u'Eduskuntaryhmät',   
}

def get_field_el(doc, field):
    el_list = doc.xpath('//div[@class="doclist-items"]/div[@class="listborder"]/table//th')
    for el in el_list:
        s = el.text.split(':')[0].strip()
        if s == FIELD_MAP[field]:
            td = el.getnext()
            if td.tag != 'td':
            	raise ParseError('expecting td element')
            return td
    return None

class MemberImporter(Importer):
    LIST_URL= '/triphome/bin/thw/trip/?${base}=hetekaue&${maxpage}=10001&${snhtml}=hex/hxnosynk&${html}=hex/hx4600&${oohtml}=hex/hx4600&${sort}=lajitnimi&nykyinen=$+and+vpr_alkutepvm%3E=22.03.1991'
    MP_INFO_URL = '/triphome/bin/hex5000.sh?hnro=%d&kieli=su'
    DATE_MATCH = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'

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
        mp_info['given_names'] = given_names

        td = get_field_el(doc, 'phone')
        if td != None:
            mp_info['phone'] = td.text.strip()

        td = get_field_el(doc, 'email')
        if td != None:
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

        td = get_field_el(doc, 'home_county')
        if td != None:
            mp_info['home_county'] = td.text.strip()

        td = get_field_el(doc, 'districts')
        el_list = td.xpath('ul/li')
        da_list = []
        for el in el_list:
            district, date_range = el.text.strip().split('  ')
            dates = date_range.split(' - ')
            da = {'district': district, 'begin': self.convert_date(dates[0])}
            if len(dates) > 1:
                da['end'] = dates[1]
            da_list.append(da)
        mp_info['districts'] = da_list

        td = get_field_el(doc, 'parties')
        el_list = td.xpath('ul/li')
        pa_list = []
        for el in el_list:
            a_el = el.xpath('a')
            if not a_el:
                # Strip text within parentheses
                m = re.match(r'([^\(]*)\([^\)]+\)(.+)', el.text)
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

        return mp_info

    def save_member(self, mp_info):
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
        mp.save()

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
    

