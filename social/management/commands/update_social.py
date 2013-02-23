import logging
import time
import datetime
import calendar
import pyfaceb

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.conf import settings
from social.models import Feed
from social.utils import FeedUpdater, UpdateError

class Command(BaseCommand):
    help = "Update social media feeds"
    option_list = BaseCommand.option_list + (
        make_option('--cached', action='store_true', dest='cached', default=False,
            help='Use local cache for HTTP requests'),
    )

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        if options['cached']:
            import requests_cache
            requests_cache.install_cache("update-social")
        self.updater = FeedUpdater(self.logger)
        self.updater.update_feeds()
