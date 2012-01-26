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
