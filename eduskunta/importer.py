import re
import os
import logging
from lxml import etree, html
from utils.http import HttpFetcher


class ParseError(Exception):
    def __init__(self, value):
         self.value = value
    def __str__(self):
         return repr(self.value)

class Importer(object):
    URL_BASE = 'http://www.eduskunta.fi'
    # regular expressions
    DATE_MATCH = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'

    def convert_date(self, s):
        m = re.match(self.DATE_MATCH, s)
        if not m:
            raise ParseError("Invalid date (%s)" % s)
        g = m.groups()
        return '-'.join((g[2], g[1], g[0]))

    replace = False

    def __init__(self, http_fetcher=None, logger=None):
        if not http_fetcher:
            http_fetcher = HttpFetcher()
        self.http = http_fetcher
        if not logger:
            logger = logging.getLogger("eduskunta import")
            logger.setLevel(logging.DEBUG)
            if not logger.handlers:
                ch = logging.StreamHandler()
                ch.setLevel(logging.DEBUG)
                formatter = logging.Formatter("%(asctime)s - %(message)s")
                ch.setFormatter(formatter)
                logger.addHandler(ch)
        self.logger = logger
    def open_url(self, *args, **kwargs):
        return self.http.open_url(*args, **kwargs)

class EduskuntaImporter(Importer):
    MINUTES_URL = '/triphome/bin/akx3000.sh?kanta=utaptk&LYH=LYH-PTK&haku=PTKSUP&kieli=su&VPVUOSI>=1999'
    LATEST_MINUTES_URL = '/triphome/bin/akx3000.sh?kanta=utaptk&uusimmat=k&VAPAAHAKU2=vpvuosi%3E=1999&haku=PTKSUP'
    VOTE_URL = 'http://www.eduskunta.fi/triphome/bin/thw.cgi/trip/?${html}=aax/aax4000&${base}=aanestysu&aanestysvpvuosi=%(year)s&istuntonro=%(plsess_nr)s&pj_kohta=%(item_nr)s&aanestysnro=%(vote_nr)s&${snhtml}=aax/aaxeiloydy'
    SGML_TO_XML = 'sgml-to-xml.sh'

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

        super(EduskuntaImporter, self).__init__(*args, **kwargs)

    def process_list_element(self, el_type, el):
        ret = {}

        special_vote = False
        children = el.getchildren()

        name_el = children[0]
        if el_type == 'votes' and name_el.tag != 'b':
            special_vote = True
        else:
            assert name_el.tag == 'b'
            name = name_el.text.strip()
            m = re.match(r'(\w+)\s(\w+/\d{4})\svp', name, re.U)
            ret['type'] = m.groups()[0]
            ret['id'] = m.groups()[1]

            link_el = children[1]
            assert link_el.tag == 'a'
            if 'sittelytiedot' in link_el.text:
                ret['process_link'] = link_el.attrib['href']
            else:
                link_el = children[2]
                assert 'HTML' in link_el.text
                ret['minutes_link'] = link_el.attrib['href']

        if el_type == 'votes':
            if not special_vote:
                assert 'process_link' in ret
                idx = 2
            else:
                idx = 0

            plsess_el = children[idx + 0]
            assert plsess_el.tag == 'a'
            s = plsess_el.text.strip()
            m = re.match(r'PTK (\w+/\d{4}) vp', s)
            assert m
            ret['plsess'] = m.groups()[0]

            id_el = children[idx + 1]
            m = re.search(r'nestys (\d+)', id_el.text)
            assert m
            ret['number'] = int(m.groups()[0])

            res_el = children[idx + 2]
            assert res_el.tag == 'a' and 'Tulos' in res_el.text_content()
            ret['results_link'] = res_el.attrib['href']

        if el_type == 'docs':
            links = [e.attrib['href'] for e in el.xpath('.//a')]
            doc_links = [link for link in links if '/bin/akxhref2.sh?' in link]
            docs = []
            for l in doc_links:
                m = re.search(r'\?\{KEY\}=(\w+)\+(\d+\w*/\d{4})', l)
                assert m
                doc = {'type': m.groups()[0], 'id': m.groups()[1]}
                doc['link'] = l
                # If it's the list item document just save the link,
                # otherwise include the associated doc.
                if doc['type'] == ret['type'] and doc['id'] == ret['id']:
                    ret['doc_link'] = doc['link']
                else:
                    docs.append(doc)
            assert 'doc_link' in ret
            ret['docs'] = docs
        elif el_type == 'minutes':
            assert 'minutes_link' in ret
        return ret

    def read_listing(self, list_type, url):
        assert list_type in ('minutes', 'votes', 'docs')

        ret = []

        s = self.open_url(url, list_type)
        doc = html.fromstring(s)
        el_list = doc.xpath(".//div[@class='listing']/div/p")
        doc.make_links_absolute(url)

        for el in el_list:
            link = {}

            parsed_el = self.process_list_element(list_type, el)
            ret.append(parsed_el)

        # Check if last page of links
        if len(el_list) >= 50:
            fwd_link = doc.xpath(".//input[@name='forward']")
            url = self.URL_BASE + fwd_link[0].attrib['value']
        else:
            url = None

        return (ret, url)

    def process_votes(self, info):
        pass

    def process_minutes_item(self, item):
        IGNORE_ITEMS = ('pjots', 'istkesk', 'istjatk', 'istuntot', 'viiva',
                        'valta', 'pmvaalit', 'ilmasia', 'muutpjn', 'vieraili',
                        'upjots')
        # FIXME: add support for valtion talousarvio 'valta'
        if item.tag in IGNORE_ITEMS:
            return
        ACCEPT_ITEMS = ('sktrunko', 'pjkohta')
        if item.tag not in ACCEPT_ITEMS:
            raise ParseError("Unknown item tag encountered: %s" % item.tag)
            return

        q = item.xpath("kohta")
        if len(q) != 1:
            # WORKAROUND
            if info['id'] == '19/2000':
                return
            raise ParseError("No item info found")
        q = q[0]
        desc_item = q.xpath("asia")
        if not len(desc_item):
            raise ParseError("No item description found" % nr)
        if len(desc_item) > 1:
            # FIXME: What to do if more than one item specified...
            pass
        desc_item = desc_item[0]
        desc_text = self.clean_text(desc_item.text)

        nr_el = q.xpath("knro")
        if len(nr_el) == 0:
            # WORKAROUND
            m = re.match(r"(\d+)\)\s+", desc_text)
            if not m:
                raise ParseError("Item number not found")
            nr = m.groups()[0]
            desc_text = re.sub(r"(\d+)\)\s+", "", desc_text)
            print nr
            print desc_text
        else:
            nr = int(nr_el[0].text)

            desc = self.clean_text(desc_item.text)
            #print "\tITM: %s" % desc


        if item.tag == 'sktrunko':
            self.process_question_time()

        """ref = sess.xpath("tulos/aanviit")
        if len(ref) != 1:
            raise ParseError("No vote reference found")
        ref = ref[0]
        session_id = (ref.attrib['aannro'], ref.attrib['istnro'], ref.attrib['vpvuosi'])
        self.process_votes(session_id)"""

    def clean_text(self, text):
        text = text.replace('\u00a0', ' ')
        # remove consecutive whitespaces
        return re.sub('\s\s+', ' ', text).strip()

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
            print link
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

        VALID_ITEM_CONTAINERS = ('pjasiat', 'upjasiat')
        for tag in VALID_ITEM_CONTAINERS:
            container_list = root.xpath(".//%s" % tag)
            for con in container_list:
                item_list = con.getchildren()
                for item in item_list:
                    self.process_minutes_item(item)

        # paalk, pjkohta, valta -> keskust -> pvuoro
        # kyskesk -> sktkesk -> sktpvuor
        item_list = root.xpath(".//pjkohta")

        item_list = root.xpath(".//kyskesk")
        for item in item_list:
            q = item.xpath("kysym")
            if len(q) != 1:
                raise ParseError("No question info found")
            q = q[0]
            #print "\tKYS: %s" % self.clean_text(q.text)

    def fetch_minutes(self):
        next_link = self.URL_BASE + self.LATEST_MINUTES_URL
        while next_link:
            el_list, next_link = self.read_listing('minutes', next_link)
            for el in el_list:
                try:
                    self.process_minutes(el)
                except Exception:
                    print "Exception!"
                    print el['minutes_link']
                    cache_fn = self.http.get_fname(el['minutes_link'], 'minutes')
                    os.remove(cache_fn)
                    raise
