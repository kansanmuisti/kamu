# -*- coding: utf-8 -*-
import re
import os
import logging
import datetime
from lxml import etree, html
from django import db
from parliament.models.member import Member
from parliament.models.session import *
from eduskunta.importer import Importer, ParseError
from eduskunta.vote import VoteImporter

SPEAKER_ADDRESSING = (
    'Herra puhemies', 'Arvoisa puhemies',
    'Arvoisa herra puhemies', 'Puhemies',
    'Herr talman',
    'Rouva puhemies', 'Arvoisa rouva puhemies',
    u'Ärade talman', u'Värderade talman',
    u'Ärade herr talman', 'Fru talman',
    u'Värderade herr talman',
    'Arvoisa eduskunnan puhemies',
    'Kunnioitettu puhemies', 'Arvoisa puhemies',
    u'Värderade fru talman',
    'Arvoisa puheenjohtaja', 'Arvon puhemies',
    'Arvoisa herra puheenjohtaja',
    'Arvostettu puhemies', 'Talman',
)

# paalk, pjkohta, valta -> keskust -> pvuoro
# kyskesk -> sktkesk -> sktpvuor

class MinutesImporter(Importer):
    MINUTES_URL = '/triphome/bin/akx3000.sh?kanta=utaptk&LYH=LYH-PTK&haku=PTKSUP&kieli=su&VPVUOSI>=1999'
    LATEST_MINUTES_URL = '/triphome/bin/akx3000.sh?kanta=utaptk&uusimmat=k&VAPAAHAKU2=vpvuosi%3E=1999&haku=PTKSUP'
    VOTE_URL = 'http://www.eduskunta.fi/triphome/bin/thw.cgi/trip/?${html}=aax/aax4000&${base}=aanestysu&aanestysvpvuosi=%(year)s&istuntonro=%(plsess_nr)s&pj_kohta=%(item_nr)s&aanestysnro=%(vote_nr)s&${snhtml}=aax/aaxeiloydy'
    DOC_ID_MATCH = r'(\w+)\s(\w+/\d{4})\svp'
    SGML_TO_XML = 'sgml-to-xml.sh'

    NON_MP_NAMES = (u'Mikko Puumalainen', u'Raimo Tammilehto', u'Kalevi Hemilä',
    		    u'Kari Häkämies')
    NON_MP_ROLES = ('Eduskunnan oikeusasiamies',
                    'Valtioneuvoston oikeuskansleri')

    TERM_DASH = u'\u2013'
    TERMS = [
        {'display_name': '2011'+TERM_DASH+'2014', 'begin': '2011-04-20', 'end': None,
         'name': '2011-2014'},
        {'display_name': '2007'+TERM_DASH+'2010', 'begin': '2007-03-21', 'end': '2011-04-19',
         'name': '2007-2010'},
        {'display_name': '2003'+TERM_DASH+'2006', 'begin': '2003-03-19', 'end': '2007-03-20',
         'name': '2003-2006'},
        {'display_name': '1999'+TERM_DASH+'2002', 'begin': '1999-03-24', 'end': '2003-03-18',
         'name': '1999-2002'},
    ]

    def __init__(self, *args, **kwargs):
        try:
            sgml_storage = kwargs.pop('sgml_storage')
        except KeyError:
            sgml_storage = 'ptk'
        try:
            xml_storage = kwargs.pop('xml_storage')
        except KeyError:
            xml_storage = 'ptkxml'

        my_path = os.path.dirname(os.path.realpath(__file__))
        self.sgml_to_xml = os.path.join(my_path, self.SGML_TO_XML)

        self.sgml_storage = os.path.join(my_path, sgml_storage)
        self.xml_storage = os.path.join(my_path, xml_storage)

        super(MinutesImporter, self).__init__(*args, **kwargs)

    def process_statement(self, st_el):
        st_info = {}
        sp_id = None
        text = []
        for ch_el in st_el.getchildren():
            if ch_el.tag in ('edustaja', 'minister'):
                e = ch_el.xpath('henkilo')[0]
                if sp_id:
                    raise ParseError("too many speaker ids")
                if 'numero' in e.attrib:
                    sp_id = int(e.attrib['numero'])
                if e.xpath('asema'):
                    st_info['role'] = self.clean_text(e.xpath('asema')[0].text)
                el_list = e.xpath('sukunimi')
                if el_list:
                    st_info['surname'] = self.clean_text(el_list[0].text)
                    # WORKAROUND
                    if st_info['surname'] == 'Mikko Puumalainen':
                        st_info['surname'] = 'Puumalainen'
                        st_info['first_name'] = 'Mikko'
                el_list = e.xpath('etunimi')
                if el_list and not 'first_name' in st_info:
                    st_info['first_name'] = self.clean_text(el_list[0].text)
            elif ch_el.tag in ('te', 'rte', 'siste'):
                if not ch_el.text:
                    assert not ch_el.getchildren()
                    continue
                s = self.clean_text(ch_el.text)
                for e in ch_el.getchildren():
                    if e.tag not in ('ala', 'li', 'yla', 'ku', 'aukko', 'alle'):
                        raise ParseError("unknown child tag: %s" % e.tag)
                    if e.tag not in ('li',) and e.text:
                        s += self.clean_text(e.text)
                    if e.tail:
                        s += self.clean_text(e.tail)
                    if e.getchildren():
                        raise ParseError("children's children, uh oh")
	        for adr in SPEAKER_ADDRESSING:
	            if s.startswith(adr + '!'):
	                s = s[len(adr) + 2:]
                        break
                text.append(s)
            elif ch_el.tag in ('pmvali', 'puhuja', 'tyhja', 'tyhjanel',
                               'istuntot', 'vieraili', 'katkos', 'aukko', 'valiots'):
                continue
            elif ch_el.tag == 'listay':
                #FIXME
                continue
            else:
                raise ParseError("unknown tag: %s" % ch_el.tag)

        st_info['speaker_id'] = sp_id
        st_info['text'] = '\n'.join(text)
        return st_info

    def process_question(self, question_el):
        el = question_el.xpath('kysym')
        if len(el) != 1:
            raise ParseError("question id not found")
        el = el[0]
        info = {'id': int(el.attrib['knro'])}
        info['subject'] = self.clean_text(el.text)
        st_list = question_el.xpath('sktkesk/sktpvuor')
        statements = []
        for st_el in st_list:
            st_info = self.process_statement(st_el)
            statements.append(st_info)
        info['statements'] = statements
        return info

    def process_budget_item(self, budget_el):
        el = budget_el.xpath('plnimi')
        if len(el) != 1:
            raise ParseError("budget class id not found")
        el = el[0]
        info = {'id': int(el.attrib['nro'])}

        el = budget_el.xpath('hallinal')
        if len(el) != 1:
            raise ParseError("budget class name not found")
        el = el[0]
        info['area'] = self.clean_text(el.text)

        st_list = []
        disc_el_list = budget_el.xpath('keskust')
        for disc_el in disc_el_list:
            for st_el in disc_el.xpath('pvuoro'):
                st_info = self.process_statement(st_el)
                st_list.append(st_info)
        info['statements'] = st_list
        return info

    def process_minutes_item(self, pl_sess_info, item):
        IGNORE_ITEMS = ('pjots', 'istkesk', 'istjatk', 'istuntot', 'viiva',
                        'pmvaalit', 'ilmasia', 'muutpjn', 'vieraili',
                        'upjots')
        # FIXME: add support for valtion talousarvio 'valta'
        if item.tag in IGNORE_ITEMS:
            if item.xpath(".//aanestys"):
                raise ParseError("vote found in an unlikely item")
            return
        ACCEPT_ITEMS = ('sktrunko', 'pjkohta', 'valta')
        if item.tag not in ACCEPT_ITEMS:
            raise ParseError("Unknown item tag encountered: %s" % item.tag)

        hdr_el = item.xpath("kohta")
        if len(hdr_el) != 1:
            # WORKAROUND
            if pl_sess_info['id'] == '19/2000':
                return
            raise ParseError("No item info found")
        hdr_el = hdr_el[0]
        desc_item = hdr_el.xpath("asia")
        if not len(desc_item):
            raise ParseError("No item description found" % nr)
        if len(desc_item) > 1:
            # FIXME: What to do if more than one item specified...
            pass
        desc_item = desc_item[0]
        desc = self.clean_text(desc_item.text)

        nr_el = hdr_el.xpath("knro")
        if len(nr_el) == 0:
            # WORKAROUND
            m = re.match(r"(\d+)\)\s+", desc)
            if not m:
                raise ParseError("Item number not found")
            nr = int(m.groups()[0])
            desc = re.sub(r"\d+\)\s+", "", desc, re.U)
        else:
            nr = int(nr_el[0].text)

        he_txt = 'Hallituksen esitys eduskunnalle'
        if desc.startswith(he_txt):
            desc = desc.replace(he_txt, 'HE:', 1)
        he_txt = 'Hallituksen esitys'
        if desc.startswith(he_txt):
            desc = desc.replace(he_txt, 'HE:', 1)

        item_info = {'nr': nr, 'desc': desc}

        doc_list = hdr_el.xpath('ak')
        docs = []
        for doc_el in doc_list:
            ref_el = doc_el.xpath('akviite')
            if len(ref_el) != 1:
                if len(doc_el.xpath('mulviite')):
                    # FIXME: add support for multiple references
                    continue
                raise ParseError("document reference not found")
            s = ref_el[0].text.strip()
            m = re.match(self.DOC_ID_MATCH, s, re.U)
            if not m:
                if s == 'HE 37/2009':
                    doc = {'type': 'HE', 'id': '37/2009'}
                elif s == 'HaVM 11/2003':
                    doc = {'type': 'HaVM', 'id': '11/2003'}
                elif s == 'TaVM 17/2002':
                    doc = {'type': 'TaVM', 'id': '17/2002'}
                else:
                    raise ParseError("invalid document reference: %s" % s)
            else:
                doc = {'type': m.groups()[0], 'id': m.groups()[1]}
            docs.append(doc)
        item_info['docs'] = docs

        if item.tag == 'sktrunko':
            item_info['type'] = 'question_time'
            q_list = []
            q_el_list = item.xpath('.//kyskesk')
            for q in q_el_list:
                q_list.append(self.process_question(q))
            item_info['questions'] = q_list
        elif item.tag == 'pjkohta':
            item_info['type'] = 'agenda_item'
            st_list = []
            disc_el_list = item.xpath('keskust')
            for disc_el in disc_el_list:
                for st_el in disc_el.xpath('pvuoro'):
                    st_info = self.process_statement(st_el)
                    st_list.append(st_info)
            if st_list:
                item_info['discussion'] = st_list
        elif item.tag == 'valta':
            item_info['type'] = 'budget'

            # sanity check
            el_list = item.xpath('.//keskust')
            for disc_el in el_list:
                p = disc_el.getparent()
                pp = p.getparent()
                if p != item and pp != item:
                    raise ParseError("aieeee!")

            disc_el_list = item.xpath('keskust')
            st_list = []
            for disc_el in disc_el_list:
                subject = disc_el.xpath('otsis')[0]
                if pl_sess_info['id'] == '51/2007':
                    if not subject.text:
                        subject.text = 'Keskustelu'
                s = self.clean_text(subject.text).strip(':')
                if s not in ('Yleiskeskustelu', 'Keskustelu'):
                    print s
                    assert False
                item_info['sub_desc'] = 'Yleiskeskustelu'
                for st_el in disc_el.xpath('pvuoro'):
                    st_info = self.process_statement(st_el)
                    st_list.append(st_info)
                if st_list:
                    item_info['discussion'] = st_list

            cl_el_list = item.xpath('paalk')
            budget_list = []
            for el in cl_el_list:
                b_info = self.process_budget_item(el)
                for bi in budget_list:
                    if bi['id'] == b_info['id']:
                        bi['statements'].extend(b_info['statements'])
                        break
                else:
                    budget_list.append(b_info)
            item_info['budget_items'] = budget_list
        else:
            raise ParseError("unknown tag %s" % item.tag)
        votes = []
        vote_list = item.xpath('.//aanestys')
        for vote_el in vote_list:
            gp = vote_el.getparent().getparent()
            if gp.tag == 'paalk':
                cl_id = int(gp.xpath('plnimi')[0].attrib['nro'])
                for b_item in budget_list:
                    if b_item['id'] == cl_id:
                        break
                else:
                    raise ParseError("vote in unknown budget item")
                sub_number = cl_id
            else:
                sub_number = None

            vote_ref_list = vote_el.xpath('tulos/aanviit')
            if len(vote_ref_list) == 0:
                if pl_sess_info['id'] == '88/2007':
                    continue
                raise ParseError("No vote reference found")
            for ref_el in vote_ref_list:
                attr = ref_el.attrib
                # WORKAROUND
                if u'\xa8' in attr['aannro']:
                    attr['aannro'] = attr['aannro'].replace(u'\xa8', '')
                vote_id = (int(attr['vpvuosi']), attr['istnro'], int(attr['aannro']))
                # WORKAROUND
                vote_pl_id = "%s/%d" % (vote_id[1], vote_id[0])
                if vote_pl_id != pl_sess_info['id']:
                    self.logger.warning("mismatch %s != %s (vote #%d)" % (vote_pl_id, pl_sess_info['id'], vote_id[2]))
                    (pid, y) = pl_sess_info['id'].split('/')
                    vote_id = (int(y), pid, vote_id[2])

                votes.append({'sub_number': sub_number, 'vote_id': vote_id})
        if votes:
            item_info['votes'] = votes

        return item_info

    def process_minutes(self, info):
        self.logger.info("processing minutes for plenary session %s/%s", info['type'], info['id'])
        s = self.open_url(info['minutes_link'], 'minutes')
        doc = html.fromstring(s)
        doc.make_links_absolute(info['minutes_link'])
        # Find the link to the SGML
        el = doc.xpath(".//a[contains(., 'Rakenteinen asiakirja')]")
        if len(el) != 1:
            raise ParseError("No link to SGML file found")
        link = el[0].attrib['href']

        fname = link.split('/')[-1]
        m = re.match(r'^([a-z0-9_]+)\.sgm$', fname)
        if not m:
            raise ParseError("SGML filename invalid")
        fname_base = m.groups()[0]
        stored_ptk_fn = '%s/%s' % (self.sgml_storage, fname)

        if os.path.exists(stored_ptk_fn):
            #self.logger.debug("SGML file found, not downloading")
            pass
        else:
            self.logger.debug("downloading SGML file")
            s = self.open_url(link, 'minutes')
            f = open(stored_ptk_fn, 'w')
            f.write(s)
            f.close()

        xml_fn = '%s/%s.xml' % (self.xml_storage, fname_base)
        if not os.path.exists(xml_fn):
            ret = os.spawnv(os.P_WAIT, self.sgml_to_xml,
                            [self.SGML_TO_XML, stored_ptk_fn, xml_fn])
            if ret:
                raise ParseError("SGML-to-XML conversion failed")

        f = open(xml_fn, 'r')
        s = f.read()
        f.close()
        root = etree.fromstring(s)

        # process ident info
        el = root
        if el.tag in ('aptk', 'eptk', 'vpjpptk'):
            return
        # FIXME (e.g. ptk_84_2003.xml)
        if el.tag == 'skt':
            return
        if el.tag != 'ptk':
            raise ParseError("Unknown root tag: %s" % el.tag)
        ver_txt = el.attrib['Versio']
        m = re.match('\w*\s*(\d\.\d)', ver_txt)
        if not m:
            raise ParseError("Version string not found ('%s')" % ver_txt)
        info['version'] = m.groups()[0]
        info['date'] = el.attrib['Ipvm']
        time_str = el.xpath('ident/kaika')[0].text
        m = re.match(r'kello (\d{1,2}\.\d{2})', time_str)
        if not m:
            m = re.match(r'kello (\d{1,2})', time_str)
        if not m:
            m = re.match(r'kello \d+ \((\d{1,2}\.\d{2})\)', time_str)
        if not m:
            raise ParseError("Invalid time: %s" % time_str)

        items = []
        VALID_ITEM_CONTAINERS = ('pjasiat', 'upjasiat')
        for tag in VALID_ITEM_CONTAINERS:
            container_list = root.xpath('.//%s' % tag)
            for con in container_list:
                item_list = con.getchildren()
                for item in item_list:
                    item_info = self.process_minutes_item(info, item)
                    if item_info:
                        items.append(item_info)
        if items:
            info['items'] = items
        self.save_minutes(info)

    def save_statement(self, item, idx, st_info):
        mp = self.mp_by_hnro.get(st_info['speaker_id'])
        if 'first_name' in st_info and 'surname' in st_info:
            name = "%s %s" % (st_info['first_name'], st_info['surname'])
        else:
            name = None
        if name and not mp:
            mp = self.mp_by_name.get(name)
        if not mp:
            if name not in self.NON_MP_NAMES:
                if st_info.get('role') in self.NON_MP_ROLES:
                    name = st_info['role']
                else:
                    print st_info
                    raise ParseError("MP not found")

        try:
            st = Statement.objects.get(item=item, index=idx)
        except Statement.DoesNotExist:
            st = Statement(item=item, index=idx)
        st.member = mp
        st.speaker_name = name
        st.speaker_role = st_info.get('role')
        st.text = st_info['text']
        st.save()

    def add_item_vote(self, item, sub_items, info):
        vote = info['vote_id']
        sub_number = info['sub_number']
        if sub_number is not None:
            item = sub_items[sub_number]

        try:
            plv = PlenaryVote.objects.get(plsess=item.plsess, number=vote[2])
        except PlenaryVote.DoesNotExist:
            plv = self.vote_importer.import_one('%d/%s/%d' % vote)
        if plv.plsess_item != item:
            plv.plsess_item = item
            plv.save()
        return

    def save_item(self, pl_sess, item_info):
        try:
            item = PlenarySessionItem.objects.get(plsess=pl_sess, number=item_info['nr'],
                                                  sub_number__isnull=True)
        except PlenarySessionItem.DoesNotExist:
            item = PlenarySessionItem(plsess=pl_sess, number=item_info['nr'])
        item.description = item_info['desc']

        if item_info['type'] == 'question_time':
            item.type = 'question'
        elif item_info['type'] == 'agenda_item':
            item.type = 'agenda'
        elif item_info['type'] == 'budget':
            item.type = 'budget'
        else:
                raise ParseError('invalid item type: %s' % item_info['type'])
        item.save()

        sub_item_by_id = {}
        sub_items = []

        if item_info['type'] == 'question_time':
            for q_info in item_info['questions']:
                try:
                    q_item = PlenarySessionItem.objects.get(plsess=pl_sess, number=item_info['nr'],
                                                            sub_number=q_info['id'])
                except PlenarySessionItem.DoesNotExist:
                    q_item = PlenarySessionItem(plsess=pl_sess, number=item_info['nr'],
                                                sub_number=q_info['id'])
                q_item.type = 'question'
                q_item.description = q_info['subject']
                q_item.save()
                for idx, st in enumerate(q_info['statements']):
                    self.save_statement(q_item, idx, st)
        elif item_info['type'] == 'agenda_item':
            if 'discussion' in item_info:
                for idx, st in enumerate(item_info['discussion']):
                    self.save_statement(item, idx, st)
        elif item_info['type'] == 'budget':
            if 'discussion' in item_info:
                for idx, st in enumerate(item_info['discussion']):
                    self.save_statement(item, idx, st)
            for b_info in item_info['budget_items']:
                try:
                    b_item = PlenarySessionItem.objects.get(plsess=pl_sess, number=item_info['nr'],
                                                            sub_number=b_info['id'])
                except PlenarySessionItem.DoesNotExist:
                    b_item = PlenarySessionItem(plsess=pl_sess, number=item_info['nr'],
                                                sub_number=b_info['id'])
                b_item.type = 'budget'
                b_item.description = item.description
                b_item.sub_description = b_info['area']
                b_item.save()
                for idx, st in enumerate(b_info['statements']):
                    self.save_statement(b_item, idx, st)
                sub_item_by_id[b_item.sub_number] = b_item
                sub_items.append(b_item)

        if 'votes' in item_info:
            for vote in item_info['votes']:
                self.add_item_vote(item, sub_item_by_id, vote)

        item.count_related_objects()
        item.save()
        for sub_item in sub_items:
            sub_item.count_related_objects()
            sub_item.save()

    def save_minutes(self, info):
        try:
            pl_sess = PlenarySession.objects.get(origin_id=info['id'])
            if not self.replace and pl_sess.origin_version == info['version']:
                return
        except PlenarySession.DoesNotExist:
            pl_sess = PlenarySession(origin_id=info['id'])
        pl_sess.name = info['id']
        term = Term.objects.get_for_date(info['date'])
        pl_sess.term = term
        pl_sess.date = info['date']
        pl_sess.info_link = info['minutes_link']
        pl_sess.url_name = pl_sess.origin_id.replace('/', '-')
        pl_sess.import_time = datetime.datetime.now()
        pl_sess.origin_version = info['version']
        pl_sess.save()

        if 'items' in info:
            for item_info in info['items']:
                self.save_item(pl_sess, item_info)

    def import_terms(self):
        for term in self.TERMS:
            try:
                nt = Term.objects.get(name=term['name'])
                if not self.replace:
                    continue
            except Term.DoesNotExist:
                self.logger.info(u'Adding term %s' % term['display_name'])
                nt = Term()
            nt.name = term['name']
            nt.begin = term['begin']
            nt.end = term['end']
            nt.display_name = term['display_name']
            if 'visible' in term:
                nt.visible = term['visible']
            nt.save()

    def _make_mp_dicts(self):
        mp_list = Member.objects.all()
        mpd = {}
        for mp in mp_list:
            mpd[int(mp.origin_id)] = mp
        self.mp_by_hnro = mpd
        mpd = {}
        for mp in mp_list:
            mpd[mp.get_print_name()] = mp
        self.mp_by_name = mpd

    def import_minutes(self):
        self.vote_importer = VoteImporter(http_fetcher=self.http, logger=self.logger)
        self._make_mp_dicts()
        next_link = self.URL_BASE + self.LATEST_MINUTES_URL
        while next_link:
            el_list, next_link = self.read_listing('minutes', next_link)
            for el in el_list:
                """year = int(el['id'].split('/')[1])
                if year > 2006:
                    continue"""
                self.process_minutes(el)
                db.reset_queries()

