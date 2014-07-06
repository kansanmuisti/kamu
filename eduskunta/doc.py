# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime, timedelta
from lxml import etree, html
from django import db
from eduskunta.importer import Importer, ParseError
from eduskunta.vote import VoteImporter
from utils.http import HTTPError
from parliament.models import Document, Keyword, DocumentProcessingStage, Member, DocumentSignature

DOC_LIST_URL = "http://www.eduskunta.fi/triphome/bin/vex3000.sh?TUNNISTE=%s&PVMVP1=1999"
#DOC_LIST_URL = "http://www.eduskunta.fi/triphome/bin/vex3000.sh?TUNNISTE=%s&PVMVP1=2003&PVMVP2=2006"
DOC_DL_URL = "http://www.eduskunta.fi/triphome/bin/akxhref2.sh?{KEY}=%s+%s"
DOC_PROCESS_URL = "http://www.eduskunta.fi/triphome/bin/vex3000.sh?TUNNISTE=%s+%s"
HE_URL = "http://217.71.145.20/TRIPviewer/temp/TUNNISTE_HE_%i_%i_fi.html"
DOC_TYPES = {
    'HE': 'gov_bill',
    'LA': 'mp_prop',
    'KK': 'written_ques',
    #"TPA", "TA", "KA", "LTA",
    #"VK", "VNT",
    #"KK", "TAA"
}

SKIP_DOCS = [
    'KA 4/2008', 'KA 6/2007', 'YmVM 10/2006', 'HE 103/2004',
    'LA 4/2003',
    'HE 113/2011', # corrupt HTML representation
    'HE 149/2012', # temporarily
    'LA 21/2011', # 'Ilmoitus peruuttamisesta' missing
    'LA 48/2012', # missing date of committee hearing
    'HE 273/2009', # ???
    'KK 180/2012', # SGML doc not found
    'HE 214/2013', # corrupt HTML
]

def should_download_doc(doc):
    if doc['type'] not in DOC_TYPES and not doc['type'].endswith('VM'):
        return False
    # Disable downloading of committee reports for now.
    if doc['type'].endswith('VM'):
        return False
    if "%s %s" % (doc['type'], doc['id']) in SKIP_DOCS:
        return False
    return True

class DocImporter(Importer):
    SGML_TO_XML = 'sgml-to-xml.sh'

    def __init__(self, *args, **kwargs):
        try:
            sgml_storage = kwargs.pop('sgml_storage')
        except KeyError:
            sgml_storage = 'doc_sgml'
        try:
            xml_storage = kwargs.pop('xml_storage')
        except KeyError:
            xml_storage = 'doc_xml'

        my_path = os.path.dirname(os.path.realpath(__file__))
        self.sgml_to_xml = os.path.join(my_path, self.SGML_TO_XML)

        self.sgml_storage = os.path.join(my_path, sgml_storage)
        self.xml_storage = os.path.join(my_path, xml_storage)
        self.doc_type = "docs"

        super(DocImporter, self).__init__(*args, **kwargs)

    def fix_id_quirks(self, info):
        if info['type'] == 'HE' and info['id'] == '45/1006':
            info['id'] = '45/2006'

    def handle_processing_stages(self, info, html_doc):
        doc_name = "%s %s" % (info['type'], info['id'])

        status_map = {
            1: 'upcoming',
            2: 'in_progress',
            3: 'finished'
        }
        names = {'vireil': ('intro', (u'Annettu eduskunnalle', u'Aloite jätetty')),
                 'lahete': ('debate', u'Lähetekeskustelu'),
                 'valiok': ('committee', u'Valiokuntakäsittely'),
                 'poydal': ('agenda', u'Valiokunnan mietinnön pöydällepano'),
                 '1kasit': ('1stread', u'Ensimmäinen käsittely'),
                 '2kasit': ('2ndread', u'Toinen käsittely'),
                 '3kasit': ('3ndread', u'Kolmas käsittely'),
                 'paat': ('finished', None),
                 'akasit': ('onlyread', u'Ainoa käsittely'),
                 'akja2k': ('only2read', u'Ainoa ja toinen käsittely'),
                 '3kjaak': ('only3read', u'Kolmas ja ainoa käsittely'),
                 'peru': ('cancelled', u'Ilmoitus peruuttamisesta'),
                 'rauennut': ('lapsed', None),
                 'raue': ('lapsed', None),
                 'jatlep': ('suspended', None),
        }
        finishing_phases = ('3ndread', '2ndread', 'onlyread', 'only2read', 'only3read',
                            'cancelled', 'lapsed', 'lapsed')

        img_els = html_doc.xpath("//div[@id='vepsasia-kasittely']/img")
        assert len(img_els)
        phases = []
        for img in img_els:
            s = img.attrib['src']
            m = re.match('/thwfakta/yht/kuvat/palkki/ve([a-z0-9]+)_(\d)\.gif', s)
            phase = m.groups()[0]
            status = int(m.groups()[1])
            status = status_map[status]
            if not phase in names:
                raise ParseError("unknown processing phase %s" % phase)
            l = names[phase]
            phase = l[0]
            phases.append((phase, status, l[1]))

        last_phase = phases[-1][0]
        phase_list = []
        for idx, (phase, status, el_name) in enumerate(phases):
            if not el_name or status not in ('in_progress', 'finished'):
                continue
            box_el_list = html_doc.xpath("//div[@class='listborder']//h2")
            # quirks
            if doc_name in ('HE 25/2009', 'HE 57/2014', 'HE 29/2014') and phase == '2ndread':
                el_name = names['akja2k'][1]
            if doc_name in ('HE 29/2014', 'HE 3/2014', 'HE 215/2013', 'HE 203/2013') and phase == 'only2read':
                phase = '2ndread'
                el_name = names['2kasit'][1]
            if doc_name == 'HE 112/2011':
                if phase == '2ndread':
                    continue
                if phase == '1stread':
                    phase = 'onlyread'
                    el_name = names['akasit'][1]

            finishing_phase = None
            for box_el in box_el_list:
                s = box_el.text_content().strip().strip('.')
                if isinstance(el_name, tuple):
                    if s not in el_name:
                        continue
                else:
                    if el_name != s:
                        continue
                parent_el = box_el.getparent().getparent()
                break
            else:
                if phase == 'committee' and last_phase in ('cancelled', 'lapsed'):
                    continue
                self.logger.warning("processing stage '%s' not found" % el_name)
                continue
            if phase == 'committee':
                el_list = parent_el.xpath(".//div[contains(., 'Valmistunut')]")
                date_list = []
                for date_el in el_list:
                    date = date_el.tail.strip()
                    (d, m, y) = date.split('.')
                    date = '-'.join((y, m, d))
                    date_list.append(date)
                if not date_list and last_phase in ('cancelled', 'lapsed'):
                    continue
                if not date_list:
                    self.logger.warning("date not found for committee phase")
                    continue
                date = max(date_list)
            else:
                date_el = parent_el.xpath(".//div[.='Pvm']")
                assert len(date_el) == 1
                date = date_el[0].tail.strip()
                (d, m, y) = date.split('.')
                date = '-'.join((y, m, d))

            if phase == 'finished':
                finishing_phase = idx

            phase_list.append((idx, phase, date))
            #print "%s: %s" % (phase, date)

        if not finishing_phase:
            for p in phases:
                if p[0] == 'finished' and p[1] != 'upcoming':
                    is_finished = True
                    break
            else:
                is_finished = False
            if is_finished:
                for p in phase_list:
                    if p[1] in finishing_phases and p[1] != 'upcoming':
                        finishing_phase = p
                        break
                assert finishing_phase, 'Finishing phase not found'

                idx = finishing_phase[0] + 1
                max_idx = max([x[0] for x in phase_list])
                assert max_idx < idx
                phase_list.append((idx, 'finished', finishing_phase[2]))

        info['phases'] = phase_list

    def handle_question(self, info, html_doc):
        el_list = html_doc.xpath("//div[@class='listborder']//h2")
        stages = {}
        for el in el_list:
            s = self.clean_text(el.text_content())
            if unicode(s) in (u'Asiasanat', u'Päätökset'):
                continue
            date_el = el.xpath("../..//div[.='Pvm']")
            if not date_el:
                continue
            assert len(date_el) == 1
            date = date_el[0].tail.strip()
            (d, m, y) = date.split('.')
            date = '-'.join((y, m, d))
            stages[s] = date
        phase_list = []
        phase_list.append((0, 'intro', stages[u'Kysymys jätetty']))
        if u'Annettu tiedoksi ministeriölle' in stages:
            phase_list.append((1, 'agenda', stages[u'Annettu tiedoksi ministeriölle']))
        if 'Vastaus annettu' in stages:
            phase_list.append((2, 'finished', stages[u'Vastaus annettu']))
        info['phases'] = phase_list

    def fetch_processing_info(self, info):
        url = DOC_PROCESS_URL % (info['type'], info['id'])
        self.logger.info('updating processing info for %s %s' % (info['type'], info['id']))
        s = self.open_url(url, 'docs')
        html_doc = html.fromstring(s)

        subj_el = html_doc.xpath(".//div[@class='listing']/div[1]/div[1]/h3")
        assert len(subj_el) == 1
        info['subject'] = self.clean_text(subj_el[0].text)

        if info['type'] == 'KK':
            self.handle_question(info, html_doc)
        else:
            self.handle_processing_stages(info, html_doc)

        kw_list = []
        kw_el_list = html_doc.xpath(".//div[@id='vepsasia-asiasana']//div[@class='linkspace']/a")
        for kw in kw_el_list:
            kw = kw.text.strip()
            kw_list.append(kw)
        if not len(kw_list):
            info['error'] = "No keywords"
            self.logger.warning("No keywords associated with document")
        info['keywords'] = kw_list

        return info

    def parse_te_paragraphs(self, root_el):
        p_list = root_el.xpath('//te')
        paras = []
        for p_el in p_list:
            text = self.clean_text(p_el.text_content())
            paras.append(text)
        return '\n'.join(paras)

    def parse_mp(self, mp_el):
        d = {}
        first = mp_el.xpath('etunimi')[0]
        last = mp_el.xpath('sukunimi')[0]
        d['first_name'] = self.clean_text(first.text_content())
        d['last_name'] = self.clean_text(last.text_content())
        d['id'] = mp_el.attrib['numero']
        return d

    def parse_signatures(self, root_el):
        sign_el = root_el.xpath('//allekosa')
        assert len(sign_el) in (1, 2)
        sign_el = sign_el[0]
        date = sign_el.xpath('paivays')[0].attrib['pvm']
        signers = sign_el.xpath('edustaja/henkilo')
        assert len(signers) > 0
        sign_list = []
        for signer in signers:
            d = self.parse_mp(signer)
            d['date'] = date
            sign_list.append(d)
        return sign_list

    def parse_author(self, root_el):
        author_el = root_el.xpath('.//ident/evtulo/edustaja/henkilo')
        assert len(author_el) == 1, "Too many 'evtulo' fields (%d)" % len(author_el)
        author_el = author_el[0]
        author = self.parse_mp(author_el)
        return author

    def import_sgml_doc(self, info):
        url = DOC_DL_URL % (info['type'], info['id'])
        xml_fn = self.download_sgml_doc(info, url)
        if not xml_fn:
            return None
        f = open(xml_fn, 'r')
        root = html.fromstring(f.read())
        f.close()

        el_list = root.xpath('.//ident/nimike')
        assert len(el_list) >= 1
        el = el_list[0]
        text = self.clean_text(el.text)
        self.logger.info('%s %s: %s' % (info['type'], info['id'], text))
        info['subject'] = text

        if info['type'].endswith('VM'):
            xpath_list = ('.//asianvir', './/emasianv')
        elif info['type'] == 'KK':
            xpath_list = (".//kysosa[@kieli='suomi']//peruste",)
        else:
            xpath_list = ('.//peruste', './/paasis', './/yleisper')
        for xpath in xpath_list:
            l = root.xpath(xpath)
            if not len(l):
                continue
            assert len(l) == 1
            target_el = l[0]
            break
        else:
            raise ParseError('Summary section not found')

        info['summary'] = self.parse_te_paragraphs(target_el)
        if info['type'] in ('KK', 'LA'):
            if info['type'] == 'KK':
                author_root = root.xpath(".//kysosa[@kieli='suomi']")
                assert len(author_root) == 1
                author_root = author_root[0]
            else:
                author_root = root

            info['author'] = self.parse_author(author_root)
            info['signatures'] = self.parse_signatures(author_root)
        return info

    def parse_he(self, info, he_str):
        html_doc = html.fromstring(he_str)
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
            self.logger.error("no header found (doc len %d)" % len(he_str))
            info['error'] = "No header found"
            return info
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
                    'LLperustelut', 'LLNormaali-0020Char', 'Normaali', 'LLSisallysluettelo')
        if 'class' in elem.attrib and elem.attrib['class'] not in BREAK_CLASS:
            self.logger.error("Mystery class: %s" % elem.attrib)
            info['error'] = "Invalid CSS class"
            return info
        if not p_list:
            self.logger.error("No summary found")
            info['error'] = "No summary found"
            return info

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
        info['summary'] = '\n'.join(text_list)
        return info

    def import_he(self, info):
        (num, year) = info['id'].split('/')
        url = HE_URL % (int(num), int(year))
        s = self.http.open_url(url, self.doc_type, error_ok=True)
        # If opening the doc failed, we try some workarounds.
        if not s:
            (s, url) = self.open_url(info['info_link'], self.doc_type, return_url=True)
            if '<!-- akxereiloydy.thw -->' in s or '<!-- akx5000.thw -->' in s:
                self.logger.error('not found!')
                return info
            html_doc = html.fromstring(s)
            frames = html_doc.xpath(".//frame")
            link_elem = None
            for f in frames:
                if f.attrib['src'].startswith('temp/'):
                    link_elem = f
                    break
            html_doc.make_links_absolute(url)
            url = link_elem.attrib['src']
            self.logger.info('HE doc generated and found')
            s = self.http.open_url(url, self.doc_type)
        # First check if's not a valid HE doc, the surest way to
        # detect it appears to be the length. *sigh*
        if len(s) < 1500:
            self.logger.warning("just PDF version found (doc len %d)" % len(s))
            info['error'] = "Only PDF version available"
            return info
        if len(s) > 4*1024*1024:
            self.logger.error('response too big (%d bytes)' % len(s))
            info['error'] = "Too big response"
            return info
        return self.parse_he(info, s)

    def save_stages(self, doc, info):
        for st in info['phases']:
            args = {'doc': doc, 'index': st[0]}
            try:
                st_obj = DocumentProcessingStage.objects.get(**args)
            except DocumentProcessingStage.DoesNotExist:
                st_obj = DocumentProcessingStage(**args)
            st_obj.stage = st[1]
            st_obj.date = st[2]
            st_obj.save()

    def save_keywords(self, doc, info):
        old_kws = set([kw.name for kw in doc.keywords.all()])
        new_kws = set(info['keywords'])
        if old_kws == new_kws:
            doc.keywords_changed = False
            return

        doc.keywords_changed = True
        for kw in info['keywords']:
            try:
                kw_obj = Keyword.objects.get(name=kw)
            except Keyword.DoesNotExist:
                self.logger.info("Adding new keyword: %s" % kw)
                kw_obj = Keyword(name=kw)
                kw_obj.save()
            doc.keywords.add(kw_obj)

    def save_signatures(self, doc, info):
        for sign in info['signatures']:
            member = Member.objects.get(origin_id=sign['id'])
            assert sign['first_name'] in member.given_names or sign['last_name'] == member.surname
            try:
                obj = DocumentSignature.objects.get(doc=doc, member=member)
            except DocumentSignature.DoesNotExist:
                obj = DocumentSignature(doc=doc, member=member)
            obj.date = sign['date']
            obj._updated = True
            obj.save()

    @db.transaction.commit_on_success
    def import_doc(self, info):
        url = DOC_DL_URL % (info['type'], info['id'])
        info['info_link'] = url
        self.fix_id_quirks(info)
        if not should_download_doc(info):
            self.logger.warning("skipping %s %s" % (info['type'], info['id']))
            return None

        origin_id = "%s %s" % (info['type'], info['id'])
        try:
            doc = Document.objects.get(origin_id=origin_id)
        except Document.DoesNotExist:
            doc = Document(origin_id=origin_id)

        if 'update_time' in info:
            doc.mark_checked()
            if doc.last_modified_time and doc.last_modified_time >= info['update_time'] and not self.replace:
                self.logger.debug("%s %s not updated" % (info['type'], info['id']))
                doc.save(update_fields=['last_checked_time'])
                return None
            else:
                self.logger.debug("%s %s updated %s (checked %s)" % (
                    info['type'], info['id'], info['update_time'], doc.last_modified_time
                ))
        else:
            if doc.pk and not self.replace:
                return doc

        doc.type = DOC_TYPES[info['type']]
        doc.name = origin_id

        info = self.fetch_processing_info(info)

        if info['type'] == 'HE':
            self.import_he(info)
        else:
            ret = self.import_sgml_doc(info)
            if not ret:
                return None
        s = "%s %s" % (info['type'], info['id'])
        doc.subject = info['subject']
        if 'summary' in info:
            doc.summary = info['summary']
        if 'error' in info:
            doc.error = info['error']
        else:
            doc.error = None
        # Figure out the document date through the intro stage.
        for st in info['phases']:
            (idx, stage, date) = st
            if stage == 'intro':
                doc.date = date
                break
        if doc.date is None:
            raise ParseError("Document date could not be determined")
        doc.info_link = info['info_link']
        if 'sgml_link' in info:
            doc.sgml_link = info['sgml_link']
        if 'author' in info:
            doc.author = Member.objects.get(origin_id=info['author']['id'])

        doc.mark_modified()
        doc.save()

        self.save_stages(doc, info)
        self.save_keywords(doc, info)
        if 'signatures' in info:
            self.save_signatures(doc, info)

        # The keywords are saved only at this point. We'll save it again in order
        # to create the proper KeywordActivity objects.
        doc._updated = True
        doc.save()

        return doc

    """def output_doc(self, f, info):
        phases = ('intro', 'debate', 'committee', '1stread', ('2ndread', 'onlyread', 'only2read'))
        intro_date = info['phases'][0][2]
        if intro_date < "2002-01-01":
            return
        s = ''
        for p in phases:
            if type(p) == str:
                p = (p,)
            for l in info['phases']:
                if l[1] in p:
                    if s:
                        s += ','
                    s += l[2]
                    break
            else:
                if '1stread' in p:
                    s += ','
                    continue
                self.skipped += 1
                print "skip (%d)" % self.skipped
                return
        f.write('"%s %s",%s\n' % (info['type'], info['id'], s))
    """
    def import_docs(self, **options):
        single = options.get('single', None)
        if single:
            info = {}
            arr = single.split(' ')
            info['type'] = arr[0]
            info['id'] = arr[1]
            doc = self.import_doc(info)
            return

        types = "(%s)" % '+or+'.join(DOC_TYPES.keys())
        url = DOC_LIST_URL % types

        from_year = options.get('from_year', None)
        if from_year:
            url += '&PVMVP2=%s' % from_year

        from_id = options.get('from_id', None)

        self.logger.info("Fetching base list URL and creating session")
        s = self.open_list_url(url, 'docs-list')
        root = html.fromstring(s)
        input_el = root.xpath('//input[@name="backward"]')
        assert len(input_el) == 1
        url = 'http://www.eduskunta.fi' + input_el[0].attrib['value']

        list_item_count = 500
        self.full_update = options.get('full')

        url = url.replace('${MAXPAGE}=51', '${MAXPAGE}=%s' % (list_item_count + 1))
        url = url.replace('${TRIPSHOW}=format=vex4050', '${TRIPSHOW}=format=vex4100')

        self.skipped = 0
        self.updated = 0

        while url:
            print url
            updated_begin = self.updated
            ret = self.read_listing('docs', url)
            doc_list = ret[0]
            fwd_link = ret[1]

            for idx, info in enumerate(doc_list):
                assert info['type'] in DOC_TYPES
                doc_id = '%s %s' % (info['type'], info['id'])
                self.logger.info("[%d/%d] document %s" %
                    (idx + 1, len(doc_list), doc_id))

                if from_id:
                    if from_id.upper() != doc_id:
                        continue
                    from_id = None

                doc = self.import_doc(info)
                if doc and getattr(doc, '_updated', False):
                    self.updated += 1
                db.reset_queries()
            url = fwd_link

            updated_this_round = self.updated - updated_begin
            if not updated_this_round and not self.full_update:
                break

        yesterday = datetime.now() - timedelta(days=1)
        doc_list = Document.objects.filter(keywords__isnull=True).order_by('date')
        q = db.models.Q(last_checked_time__lte=yesterday) | db.models.Q(last_checked_time__isnull=True)
        doc_list = doc_list.filter(q)
        self.logger.info("Updating %d documents without keywords" % len(doc_list))
        for idx, doc in enumerate(doc_list):
            arr = doc.name.split(' ')
            info = {'type': arr[0], 'id': arr[1]}
            self.logger.info("[%d/%d] document %s %s" %
                (idx + 1, len(doc_list), info['type'], info['id']))
            self.import_doc(info)
