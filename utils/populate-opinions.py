#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import http_cache
from optparse import OptionParser

from django.core.management import setup_environ

my_path = os.path.abspath(os.path.dirname(__file__))
app_path = os.path.normpath(my_path + '/..')
app_base = app_path + '/'

# We need a path like '<app_path>/utils:<app_path>:<app_path>/..'
# The first one is inserted by python itself. The order is important to
# guarantee that we'll import the proper app specific module in case there
# is also a generic (non-app-specific) module with the same name later in
# the path.
sys.path.insert(1, app_path)
sys.path.insert(2, os.path.normpath(app_path + '/..'))

from kamu import settings
setup_environ(settings)

import hs2011_opinions

parser = OptionParser()
parser.add_option('--cache', action='store', type='string', dest='cache',
                  help='use cache in directory CACHE')

(opts, args) = parser.parse_args()

if opts.cache:
    http_cache.set_cache_dir(opts.cache)

hs2011_opinions.parse()
