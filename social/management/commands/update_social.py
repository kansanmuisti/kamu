import logging
import time
import datetime
import calendar
import pyfaceb

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.conf import settings
from social.models import Feed
from social.utils import FeedUpdater, UpdateError

class Command(BaseCommand):
    help = "Update social media feeds"

    def handle(self, *args, **options):
        import requests_cache
        requests_cache.configure("update-social")
        self.logger = logging.getLogger(__name__)
        self.updater = FeedUpdater(self.logger)
        self.updater.update_feeds()
