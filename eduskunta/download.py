import os
import collections
import requests
import json
import requests_cache
from dateutil import parser as dateutil_parser
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import TerminalTrueColorFormatter 


from pprint import pprint
from lxml import etree

#requests_cache.install_cache('eduskunta')

def get_persistent_int(name, default=None):
    path = f"last_ids/{name}.txt"
    try:
        with open(path, 'r') as f:
            return int(f.read())
    except IOError:
        return default

def set_persistent_int(name, value):
    path = f"last_ids/{name}.txt"
    with open(path, 'w') as f:
        f.write(str(value))

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

def dump_salidb(name, pk_name):
    url = lambda pk: f"https://avoindata.eduskunta.fi/api/v1/tables/{name}/batch?pkStartValue={pk}&pkName={pk_name}"
    pk = get_persistent_int(name, 0)
    while True:
        print(name, pk)
        data = requests.get(url(pk))
        data.raise_for_status()
        data = data.json()
        pkcol = data['columnNames'].index(pk_name)
        
        if len(data['rowData']) == 0: break

        maxpk = max(int(d[pkcol]) for d in data['rowData'])

        fname = f"xml/salidb/{name}-{pk}-{maxpk}.json"
        
        json.dump(data, open(fname, 'w'))
        pk = maxpk + 1
        set_persistent_int(name, pk)

def dump_salidbs():
    data = requests.get("https://avoindata.eduskunta.fi/api/v1/tables/PrimaryKeys/rows").json()
    cols = data['columnNames']
    rows = [dict(zip(cols, row)) for row in data['rowData']]
    for row in rows:
        if not row['TableName'].startswith('SaliDB'): continue
        dump_salidb(row['TableName'], row['PrimaryKeyName'])

if __name__ == '__main__':
    get_new_vaski_messages()
    dump_salidbs()
