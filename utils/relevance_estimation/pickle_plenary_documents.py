#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import shelve
import urllib.request, urllib.parse, urllib.error

sys.path.append(os.path.abspath(__file__ + '/../../../..'))
sys.path.append(os.path.abspath(__file__ + '/../../..'))
from django.core.management import setup_environ
from kamu import settings
setup_environ(settings)

from kamu.opinions.models import Question
from kamu.votes.models import Session

he_uri = 'http://217.71.145.20/TRIPviewer/temp/TUNNISTE_HE_%i_%i_fi.html'


def get_plenary_documents(dst):
    hematch = re.compile('HE (\d+)/(\d{4})')
    for session in Session.objects.all():
        for doc in session.sessiondocument_set.all():
            match = hematch.match(doc.name)
            if match is None:
                continue

            name = str(doc.name)
            if name in dst:
                continue

            (number, year) = list(map(int, match.groups()))
            uri = he_uri % (number, year)

            print('Fetching data for %s' % name, file=sys.stderr)
            try:
                data = urllib.request.urlopen(uri).read()
            except IOError as e:
                print('Reading data for %s failed' % name, file=sys.stderr)
                continue
            dst[name] = data


if __name__ == '__main__':
    dst = shelve.open(sys.argv[1])
    try:
        get_plenary_documents(dst)
    finally:
        dst.close()

