#!/usr/bin/python

import os
import sys
from . import http_cache
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

from django.db import connection, transaction
from django import db

from . import funding_2007, funding_2011

parser = OptionParser()
parser.add_option('--f2007', action='store', type='string', dest='f2007',
                  help='parse 2007 funding from supplied file')
parser.add_option('--f2011', action='store', type='string', dest='f2011',
                  help='parse 2011 funding')
parser.add_option('--cache', action='store', type='string', dest='cache',
                  help='use cache in directory CACHE')

(opts, args) = parser.parse_args()

if opts.cache:
    http_cache.set_cache_dir(opts.cache)
if opts.f2007:
    funding_2007.parse(opts.f2007)
if opts.f2011:
    funding_2011.parse(opts.f2011)
