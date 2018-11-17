import logging
import time
import datetime
import calendar
##import pyfaceb

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.conf import settings
from social.models import Feed
from social.utils import FeedUpdater, UpdateError

class Command(BaseCommand):
    help = "Update social media feeds"
    
    def add_arguments(self, parser):
        parser.add_argument('--cached',
            action='store_true',
            dest='cached',
            default=False,
            help='Use local cache for HTTP requests')
        parser.add_argument('--type',
            action='store',
            dest='type',
            help='Types of feed to update')
        parser.add_argument('--feed-id',
            action='store',
            dest='feed_id',
            help='Update only single feed')

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        if options['cached']:
            import requests_cache
            requests_cache.install_cache("update-social")
        self.updater = FeedUpdater(self.logger)
        update_opts = {}
        if 'type' in options and options['type']:
            update_opts['type'] = options['type'].split(',')
        update_opts['feed_id'] = options.get('feed_id', None)
        self.updater.update_feeds(**update_opts)
