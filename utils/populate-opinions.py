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
import mtv2007_opinions

parser = OptionParser()
parser.add_option('--mtv2007', action='store_true', dest='mtv2007',
                  help='use cache in directory CACHE')
parser.add_option('--hs2011', action='store_true', dest='hs2011',
                  help='use cache in directory CACHE')
parser.add_option('--cache', action='store', type='string', dest='cache',
                  help='use cache in directory CACHE')

(opts, args) = parser.parse_args()

if opts.cache:
    http_cache.set_cache_dir(opts.cache)
if opts.mtv2007:
    mtv2007_opinions.parse()
if opts.hs2011:
    hs2011_opinions.parse()
