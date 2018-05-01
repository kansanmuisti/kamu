# -*- coding: utf-8 -*-
import csv
from difflib import get_close_matches
from lxml import etree, html
from eduskunta.importer import Importer
from eduskunta.member import fix_mp_name
from parliament.models import Member, Term, Funding, FundingSource

HS_SRC_TO_TYPE = {
    'Omat varat': 'own',
    'Yksityislahjoitus': 'ind',
    'Laina': 'loan',
    'Tuntemattomat yksityislahjoittajat': 'u_ind',
    'Tuntemattomat yhteisölahjoittajat': 'u_com',
    'Tuntematon välitetty tuki': 'oth',
}

class FundingImporter(Importer):
    Y2011_URL = 'http://www2.hs.fi/extrat/hsnext/280-kaikki-ilmoitukset-rahoitusmuodossa.csv'

    def fetch_hs_funding(self):
        self.logger.debug("fetching funding from HS")
        s = self.open_url(self.Y2011_URL, 'funding')
        reader = csv.reader(s.splitlines(), delimiter=';')
        row = next(reader) # header

        mp_funding = []
        for row in reader:
            (src, mp, amount, district, party) = row
            src = self.clean_text(src.decode('iso8859-1'))
            mp = self.clean_text(mp.decode('iso8859-1'))
            l = src.split(':')
            if len(l) == 1:
                src_type = 'co'
            else:
            	hs_type = l.pop(0)
            	src = ':'.join(l)
            	if hs_type not in HS_SRC_TO_TYPE:
            	    src = "%s:%s" % (hs_type, src)
            	    src_type = 'co'
            	else:
            	    src_type = HS_SRC_TO_TYPE[hs_type]
            amount = float(amount.replace(',', '.').replace(' ', ''))
            src = self.clean_text(src)
            d = {'mp': mp, 'type': src_type, 'src': src, 'amount': amount}
            mp_funding.append(d)
        return mp_funding

    def save_funding(self, mp_funding):
        term = Term.objects.get_for_date('2011-05-01')
        for fund in mp_funding:
            names = fund['mp'].split()
            fn = '%s %s' % (names[-1], names[0])
            fn = fix_mp_name(fn)
            try:
                mp = Member.objects.get(name=fn)
            except Member.DoesNotExist:
                continue
            if fund['type'] in ('own', 'loan', 'u_ind', 'u_com'):
                src = None
            else:
                src = FundingSource.objects.get_or_create(name=fund['src'])[0]
            try:
                funding = Funding.objects.get(type=fund['type'], member=mp, source=src, term=term)
                if not self.replace:
                    continue
            except Funding.DoesNotExist:
                funding = Funding(type=fund['type'], member=mp, source=src, term=term)
            funding.amount = fund['amount']
            funding.save()

    def import_funding(self):
    	mp_funding = self.fetch_hs_funding()
        self.save_funding(mp_funding)
        return

