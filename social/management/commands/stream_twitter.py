import logging
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from social.models import *
from social.utils import *
from twython import TwythonStreamer

class Streamer(TwythonStreamer):
    def on_success(self, data):
        self.logger.info(data)
        self.updater.process_tweet(data)

    def on_error(self, status_code, data):
        self.logger.error("Twitter API returned error %d (data: %s)" % (status_code, data))

class Command(BaseCommand):
    help = "Start Twitter streaming"

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        self.updater = FeedUpdater(self.logger)
        feed_ids = Feed.objects.filter(type='TW').values_list('origin_id', flat=True)

        self.logger.info("Waiting for tweets for %d feeds" % len(feed_ids))

        stream = Streamer(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET, settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
        stream.updater = self.updater
        stream.logger = self.logger

        stream.statuses.filter(follow=','.join(feed_ids))
