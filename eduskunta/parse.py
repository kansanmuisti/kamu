from pprint import pprint
from datetime import datetime, date
import glob
import re
import pytz
import dateutil.parser
from lxml import objectify, etree
import sys


LOCAL_TZ = pytz.timezone('Europe/Helsinki')


NSMAP = {
    'ns11': 'http://www.eduskunta.fi/skeemat/siirto/2011/09/07',
    'sa': 'http://www.arkisto.fi/skeemat/sahke2/2011/01/31_vnk',
    'ns4': 'http://www.eduskunta.fi/skeemat/siirtoelementit/2011/05/17',
    'asi': 'http://www.vn.fi/skeemat/asiakirjakooste/2010/04/27',
    'asi1': 'http://www.vn.fi/skeemat/asiakirjaelementit/2010/04/27',
    'jme': 'http://www.eduskunta.fi/skeemat/julkaisusiirtokooste/2011/12/20',
    'met': 'http://www.vn.fi/skeemat/metatietokooste/2010/04/27',
    'met1': 'http://www.vn.fi/skeemat/metatietoelementit/2010/04/27',
    'org': 'http://www.vn.fi/skeemat/organisaatiokooste/2010/02/15',
    'org1': 'http://www.vn.fi/skeemat/organisaatioelementit/2010/02/15',
    'sii': 'http://www.eduskunta.fi/skeemat/siirtokooste/2011/05/17',
    'sii1': 'http://www.eduskunta.fi/skeemat/siirtoelementit/2011/05/17',
    'sis': 'http://www.vn.fi/skeemat/sisaltokooste/2010/04/27',
    'sis1': 'http://www.vn.fi/skeemat/sisaltoelementit/2010/04/27',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'he': 'http://www.vn.fi/skeemat/he/2010/04/27',
    'mix': 'http://www.loc.gov/mix/v20',
    'narc': 'http://www.narc.fi/sahke2/2010-09_vnk',
    'saa': 'http://www.vn.fi/skeemat/saadoskooste/2010/04/27',
    'saa1': 'http://www.vn.fi/skeemat/saadoselementit/2010/04/27',
    'tau': 'http://www.vn.fi/skeemat/taulukkokooste/2010/04/27',
    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
    'fra': 'http://www.eduskunta.fi/skeemat/fraasikooste/2011/01/04',
    'fra1': 'http://www.eduskunta.fi/skeemat/fraasielementit/2011/01/04',
    'vsk1': 'http://www.eduskunta.fi/skeemat/vaskielementit/2011/01/04',
    'evek': 'http://www.eduskunta.fi/skeemat/vastaus/2011/01/04',
    'vsk': 'http://www.eduskunta.fi/skeemat/vaskikooste/2011/01/04',
    'eka': 'http://www.eduskunta.fi/skeemat/eduskuntaaloite/2012/08/10',
    'kys': 'http://www.eduskunta.fi/skeemat/kysymys/2012/08/10',
    'elu': 'http://www.eduskunta.fi/skeemat/ehdotusluettelo/2014/07/28',
    'ptk': 'http://www.eduskunta.fi/skeemat/poytakirja/2011/01/28',
    'vml': 'http://www.eduskunta.fi/skeemat/mietinto/2011/01/04',
    'vas': 'http://www.eduskunta.fi/skeemat/vastalause/2011/01/04',
    'kks': 'http://www.eduskunta.fi/skeemat/kokoussuunnitelma/2011/01/28',
    'til': 'http://www.eduskunta.fi/skeemat/tilasto/2013/04/24',
    'kir': 'http://www.vn.fi/skeemat/kirjelma/2010/04/27',
    'vpa': 'http://www.eduskunta.fi/skeemat/kasittelytiedotvaltiopaivaasia/2011/03/25',
    'buk': 'http://www.vn.fi/skeemat/talousarviokooste/2011/06/14',
    'buk1': 'http://www.vn.fi/skeemat/talousarvioelementit/2011/06/14',
    'tam': 'http://www.eduskunta.fi/skeemat/talousarviokirjelma/2011/06/14',
    'lka': 'http://www.eduskunta.fi/skeemat/kasittelytiedotlausumaasia/2013/11/15',
}


def find_missing_namespaces():
    all_uris = set(NSMAP.values())
    for xml_file in glob.glob('xml/*/*/*.xml'):
        f = open(xml_file, 'r')
        out = objectify.parse(f)
        for ch in out.iter():
            ns = set(ch.nsmap.values())
            new_uris = ns - all_uris
            for uri in new_uris:
                for key, val in ch.nsmap.items():
                    if val == uri:
                        print("    '%s': '%s'" % (key, val))
                        break
                else:
                    assert False
            all_uris |= new_uris


def replace_ns(s):
    def replace(ns):
        ns = ns.groups()[0].strip('{}')
        for key, val in NSMAP.items():
            if val == ns:
                return '%s:' % key
        return ns.groups()[0]
    return re.sub(r'^(\{.*\})', replace, s)


class SaneElement:
    def __init__(self, el):
        self.el = el

    def __str__(self):
        return str(self.tag)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        return self.attrib[key]

    def xpath(self, path):
        ret = list(self.el.xpath(path, namespaces=NSMAP))
        assert len(ret) > 0, 'Path %s not found' % path

        return [SaneElement(x) for x in list(ret)]

    def xpathone(self, path):
        ret = list(self.el.xpath(path, namespaces=NSMAP))
        assert len(ret) == 1, 'Path %s not found' % path
        return SaneElement(ret[0])

    def find(self, path: str):
        ret = self.el.find(path, namespaces=NSMAP)
        if ret is not None:
            return SaneElement(ret)
        return None

    def getchildren(self):
        ret = self.el.getchildren()
        return [SaneElement(x) for x in list(ret)]

    def print(self, levels=1, out=sys.stdout, _level=0):
        ind = '  ' * _level
        line = lambda v: out.write(f"{ind}{v}\n")

        line(f"-{self}")
        for key, val in self.attrib.items():
            line(f'  @{key} = {val}')

        text = (self.text or '').strip()
        if text:
            line(f"  *{text.strip()}")

        if _level >= levels:
            return

        for child in self.getchildren():
            child.print(levels, out, _level + 1)

    @property
    def tag(self):
        return replace_ns(self.el.tag)

    @property
    def text(self):
        return self.el.text

    @property
    def attrib(self):
        return {replace_ns(key): val for key, val in self.el.attrib.items()}


class EduskuntaDoc:
    def parse_date(self, s) -> date:
        return dateutil.parser.parse(s).date()

    def parse_dt(self, s) -> datetime:
        """Parse a datetime."""
        dt = dateutil.parser.parse(s)
        if dt.tzinfo is None:
            dt = LOCAL_TZ.localize(dt)
        return dt

    def parse_identifier(self, s):
        m = re.match(r'([A-Z]+) ([0-9]+/[0-9]{4}) vp', s)
        return m.groups()

    def parse_header(self):
        obj = self.doc.xpath('//jme:JulkaisuMetatieto')[0]
        id_str = obj.attrib['met1:eduskuntaTunnus']
        self.type, self.identifier = self.parse_identifier(id_str)
        self.created_at = self.parse_date(obj.attrib['met1:laadintaPvm'])

    def __init__(self, xmlstr: str):
        self.doc = SaneElement(etree.fromstring(xmlstr))
        self.doc.print()
        self.parse_header()


class PlenarySessionDoc(EduskuntaDoc):
    def parse_item(self, el):
        el.print()
        item_number = el.xpathone('vsk1:KohtaNumero').text
        item = {}
        if el.tag == 'vsk:Asiakohta':
            item['description'] = el.xpath('.//met1:NimekeTeksti')[0].text
            print(item['description'])
            item_type, identifier = self.parse_identifier(el['met1:eduskuntaTunnus'])
            if item_type == 'SKT':
                item['type'] = 'question'
            elif item_type in (
                'HE', 'VAP', 'VAA', 'K', 'LA', 'VNT', 'VNS',
                'KAA', 'PNE', 'VK', 'ETJ', 'VN', 'LJL', 'PI',
                'KA', 'O', 'M', 'TPA'
            ):
                item['type'] = 'agenda'
            else:
                raise Exception('Unknown type: %s' % item_type)
        else:
            item['description'] = el.xpathone('.//sis1:OtsikkoTeksti').text
            item['type'] = 'agenda'

        n = item_number.split('.')
        item['number'] = int(n.pop(0))
        if n:
            item['sub_number'] = int(n.pop(0))
        else:
            item['sub_number'] = None
        self.items.append(item)

    def parse(self):
        assert self.type == 'PTK'
        self.root = root = self.doc.xpathone('//ptk:Poytakirja')
        self.begins_at = self.parse_dt(root['vsk1:kokousAloitusHetki'])
        self.ends_at = self.parse_dt(root['vsk1:kokousLopetusHetki'])
        self.version = root['met1:versioTeksti']
        self.items = []

        items = root.getchildren()
        for item in items:
            if item.tag not in ('vsk:Asiakohta', 'vsk:MuuAsiakohta'):
                continue
            self.parse_item(item)

    def to_dict(self):
        ret = {
            'name': self.identifier,
            'date': self.begins_at.date(),
            'url_name': self.identifier.replace('/', '-'),
            'origin_id': self.identifier,
            'origin_version': self.version,
        }
        return ret


if __name__ == '__main__':
    for idx, fpath in enumerate(glob.glob('xml/PlenarySessionMainPage_fi/2016/*.xml')):
        fname = fpath.split('/')[-1]
        print(fpath)
        s = open(fpath, 'r').read()
        doc = PlenarySessionDoc(s)
        doc.parse()
        if idx == 5:
            break
