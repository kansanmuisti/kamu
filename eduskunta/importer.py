import re
import os
import logging
from lxml import etree, html
from utils.http import HttpFetcher


class ParseError(Exception):
    def __init__(self, value, url=None):
        self.value = value
        self.url = url

    def __str__(self):
        return repr(self.value)


class Importer(object):
    URL_BASE = 'http://www.eduskunta.fi'
    # regular expressions
    DATE_MATCH = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'

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

    def convert_date(self, s):
        m = re.match(self.DATE_MATCH, s)
        if not m:
            raise ParseError("Invalid date (%s)" % s)
        g = m.groups()
        return '-'.join((g[2], g[1], g[0]))

    def clean_text(self, text):
        text = text.replace('\n', ' ')
        # remove consecutive whitespaces
        return re.sub(r'\s\s+', ' ', text, re.U).strip()

    def open_url(self, *args, **kwargs):
        return self.http.open_url(*args, **kwargs)
    def open_list_url(self, url, list_type, *args, **kwargs):
        return self.open_url(url, list_type + '-list', *args, **kwargs)

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

        s = self.open_list_url(url, list_type + '-list')
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

    def download_sgml_doc(self, html_url):
        s = self.open_url(html_url, self.doc_type)
        doc = html.fromstring(s)
        # Find the link to the SGML
        el = doc.xpath(".//a[contains(., 'Rakenteinen asiakirja')]")
        if len(el) != 1:
            # retry
            self.http.nuke_cache(html_url, self.doc_type)
            s = self.open_url(html_url, self.doc_type)
            doc = html.fromstring(s)
        # Find the link to the SGML
        el = doc.xpath(".//a[contains(., 'Rakenteinen asiakirja')]")

        if len(el) != 1:
            raise ParseError("No link to SGML file found")
        doc.make_links_absolute(html_url)
        link = el[0].attrib['href']

        fname = link.split('/')[-1]
        m = re.match(r'^([a-z0-9_]+)\.sgm$', fname)
        if not m:
            raise ParseError("SGML filename invalid")
        fname_base = m.groups()[0]
        stored_sgml_fn = '%s/%s' % (self.sgml_storage, fname)

        if not os.path.exists(stored_sgml_fn):
            self.logger.debug("downloading SGML file")
            try:
                s = self.open_url(link, self.doc_type)
            except HTTPError:
                # retry after nuking the cache
                self.http.nuke_cache(html_url, self.doc_type)
                self.open_url(html_url, self.doc_type)
                s = self.open_url(link, self.doc_type)
            f = open(stored_sgml_fn, 'w')
            f.write(s)
            f.close()

        xml_fn = '%s/%s.xml' % (self.xml_storage, fname_base)
        if not os.path.exists(xml_fn):
            ret = os.spawnv(os.P_WAIT, self.sgml_to_xml,
                            [self.SGML_TO_XML, stored_sgml_fn, xml_fn])
            if ret:
                raise ParseError("SGML-to-XML conversion failed")

        return xml_fn
