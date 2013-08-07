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
from eduskunta.doc import DocImporter
from utils.http import HTTPError

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
    		    u'Kari Häkämies', u'Carl Haglund')
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
            sgml_storage = 'minutes_sgml'
        try:
            xml_storage = kwargs.pop('xml_storage')
        except KeyError:
            xml_storage = 'minutes_xml'

        my_path = os.path.dirname(os.path.realpath(__file__))
        self.sgml_to_xml = os.path.join(my_path, self.SGML_TO_XML)

        self.sgml_storage = os.path.join(my_path, sgml_storage)
        self.xml_storage = os.path.join(my_path, xml_storage)
        self.doc_type = "minutes"

        super(MinutesImporter, self).__init__(*args, **kwargs)

    def process_speaker_statement(self, st_el):
        """processes a speaker statement and return a reasonable simile of an ordinary statement.

        Speaker statements do not have as much structure in the source as ordinary statements.
        Thus this method has to do some string manipulation and assumes a simple firstname-surname
        structure for the speaker name.

        This will return None, if the statement fails to parse. They are not that essential.
        """
        spk_statement = {}
        statement_text = []
        for spkst_el in st_el.getchildren():
            if spkst_el.tag == 'puhemies':
                if speaker_titlename:
                    raise ParseError('Several titles for the house speaker. Check the source and/or fix importer')
                speaker_titlename = self.clean_text(spkst_el.text)
                try:
                    speaker_name = speaker_titlename.split('uhemies ')[1]
                except:
                    # There are a few mistypes without a name for the speaker.
                    # Lets just ignore those completely, most of the speaker
                    # statements are pretty morose anyway
                    return None
                speaker_name = speaker_name.split(' ')
                if len(speaker_name) > 2:
                    raise ParseError('More than two parts to the name of house speaker.\n Title+name was: ' + speaker_titlename)
                spk_statement['first_name'] = speaker_name[0]
                spk_statement['surname'] = speaker_name[1]
            if spkst_el.tag == 'te':
                 statement_text.append(self.clean_text(spkst_el.text))
        spk_statement['type'] = "speaker"
        spk_statement['text'] = '\n'.join(statement_text)
        return spk_statement

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

        st_info['type'] = "normal"
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
        if not desc_item.text and not hdr_el.xpath("knro"):
            # WORKAROUND
            return
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
            s = self.clean_text(ref_el[0].text)
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
            # Speaker statements are special, they may appear both inside
            # and outside the discussion structure. 
            for sub_item in item:
                if sub_item.tag == 'pmpvuoro':
                    spk_statement = self.process_speaker_statement(sub_item)
                    if spk_statement:
                        st_list.append(spk_statement)
                elif sub_item.tag == 'keskust':
                    for st_el in sub_item:
                        if st_el.tag == 'pvuoro':
                            st_info = self.process_statement(st_el)
                            st_list.append(st_info)
                        elif st_el.tag == 'pmpvuoro':
                            spk_statement = self.process_speaker_statement(st_el)
                            if spk_statement:
                                st_list.append(spk_statement)
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
                if pl_sess_info['id'] in ('84/2001', '88/2007', '130/1999', '132/2012'):
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
                vote_full_id = "%d/%s/%d" % vote_id
                if vote_full_id in ('2006/43/2', '2005/130/11', '2004/78/1'):
                    continue
                votes.append({'sub_number': sub_number, 'vote_id': vote_id})
        if votes:
            item_info['votes'] = votes

        return item_info

    def process_minutes(self, info):
        self.logger.info("processing minutes for plenary session %s/%s", info['type'], info['id'])

        xml_fn = self.download_sgml_doc(info, info['minutes_link'])
        f = open(xml_fn, 'r')
        root = etree.fromstring(f.read())
        f.close()

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
        m = re.match('\w*[\s\.]*(\d\.\d)', ver_txt)
        if not m:
            raise ParseError("Version string invalid ('%s')" % ver_txt)
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
        if st_info['type'] == "normal":
            mp = self.mp_by_hnro.get(st_info['speaker_id'])
        elif st_info['type'] == "speaker":
            speaker_dispname = " ".join([st_info['first_name'], st_info['surname']])
            mp = self.mp_by_name.get(speaker_dispname)
            if not mp:
                raise ParseError('Failed to locate an MP corresponding to name of speaker')
        else:
            raise ParseError('Parser returned an unknown type of statement')
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
        st.statement_type = st_info['type']
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

        if 'docs' in item_info:
            for idx, doc in enumerate(item_info['docs']):
                doc_obj = self.doc_importer.import_doc(doc)
                if not doc_obj:
                    continue
                args = {'item': item, 'order': idx}
                try:
                    item_doc = PlenarySessionItemDocument.objects.get(**args)
                except PlenarySessionItemDocument.DoesNotExist:
                    item_doc = PlenarySessionItemDocument(**args)
                item_doc.doc = doc_obj
                item_doc.save()

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

    def import_minutes(self, options={}):
        self.vote_importer = VoteImporter(http_fetcher=self.http, logger=self.logger)
        self.doc_importer = DocImporter(http_fetcher=self.http, logger=self.logger)
        self._make_mp_dicts()
        next_link = self.URL_BASE + self.LATEST_MINUTES_URL
        while next_link:
            el_list, next_link = self.read_listing('minutes', next_link)
            for el in el_list:
                year = int(el['id'].split('/')[1])
                if 'from_year' in options:
                    if year > int(options['from_year']):
                        continue
                if 'from_id' in options:
                    if el['id'] == options['from_id']:
                        del options['from_id']
                    else:
                        continue

                self.process_minutes(el)
                db.reset_queries()

