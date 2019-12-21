import os
import collections
import requests
import requests_cache
from dateutil import parser as dateutil_parser
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import TerminalTrueColorFormatter 


from pprint import pprint
from lxml import etree

#requests_cache.install_cache('eduskunta')


def process_vaski_result(data):
    columns = data['columnNames']
    cleaned = []
    rows = data['rowData']
    for row in rows:
        d = {attr: row[idx] for idx, attr in enumerate(columns)}
        cleaned.append(d)

    return cleaned


def get_vaski_by_pk(pk):
    #resp = requests.get('https://avoindata.eduskunta.fi/api/v1/tables/VaskiData/batch?pkStartValue=1&pkName=Id')
    resp = requests.get('https://avoindata.eduskunta.fi/api/v1/tables/VaskiData/batch?pkStartValue={pk}&pkName=Id'.format(pk=pk))
    data = process_vaski_result(resp.json())

    NAMESPACES = {
        'sk': 'http://www.eduskunta.fi/skeemat/siirtokooste/2011/05/17',
        'se': 'http://www.eduskunta.fi/skeemat/siirtoelementit/2011/05/17',
        'met1': 'http://www.vn.fi/skeemat/metatietoelementit/2010/04/27'
    }
    if not data:
        raise Exception()
    for d in data:
        root = etree.fromstring(d['XmlData'])
        msg_name = root.xpath('//se:SanomatyyppiNimi', namespaces=NAMESPACES)[0].text
        created_at = root.xpath('//se:LuontiHetki', namespaces=NAMESPACES)[0].text
        d['msg_name'] = msg_name
        d['created_at'] = dateutil_parser.parse(created_at)

        if msg_name.endswith('_sv'):
            continue
        #if 'VASKI_JULKVP_Record_fi' in msg_name:
        #    s = str(etree.tostring(root, encoding='utf8', pretty_print=True), encoding='utf8')
        #    print(highlight(s, XmlLexer(), TerminalTrueColorFormatter()))

            #el = root.xpath('//met1:EduskuntaTunnus', namespaces=NAMESPACES)
        #    if el and el[0].text.startswith('HE'):
        #        print(s)
        #        exit()
        d['xml'] = root
    return data


def get_new_vaski_messages():
    counter = collections.Counter()
    latest_import = None

    try:
        with open('last_pk.txt', 'r') as f:
            pk = int(f.read())
    except IOError:
        pk = 1

    while True:
        data = get_vaski_by_pk(pk)
        new_pk = max(int(x['Id']) for x in data)
        if new_pk == pk:  # no more data
            break
        pk = new_pk
        # counter.update('-'.join(x['created_at'].split('-')[0:2]) for x in data)
        counter.update(d['msg_name'] for d in data)
        for d in data:
            if d['msg_name'].endswith('_sv'):
                continue
            path = 'xml/%s/%s/%s.xml' % (d['msg_name'].split('VASKI_JULKVP_')[1], d['created_at'].year,
                                         d['created_at'].isoformat())
            try:
                os.makedirs(os.path.dirname(path))
            except FileExistsError:
                pass

            if os.path.isfile(path):
                continue

            with open(path, 'w') as f:
                f.write(str(etree.tostring(d['xml'], encoding='utf8', pretty_print=True), encoding='utf8'))

            if not latest_import or d['created_at'] < latest_import:
                latest_import = d['created_at']

        for msg, count in sorted(counter.items()):
            print("%s\t%s" % (msg, count))
        print(pk)
        with open('last_pk.txt', 'w') as f:
            f.write(str(pk))


get_new_vaski_messages()
