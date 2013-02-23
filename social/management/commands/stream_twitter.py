import logging
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from social.models import *
from social.utils import *
from tweetstream import FilterStream, ConnectionError

class Command(BaseCommand):
    help = "Start Twitter streaming"

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        self.updater = FeedUpdater(self.logger)
        feed_ids = Feed.objects.filter(type='TW').values_list('origin_id', flat=True)

        self.logger.info("Waiting for tweets for %d feeds" % len(feed_ids))
        reconnect_timeout = 1
        while True:
            stream = FilterStream(settings.TWITTER_USERNAME, settings.TWITTER_PASSWORD,
                                  follow=feed_ids)
            try:
                for tweet in stream:
                    reconnect_timeout = 1
                    self.updater.process_tweet(tweet)
            except ConnectionError as e:
                self.logger.error("%s" % e)
                reconnect_timeout = 2 * reconnect_timeout
                time.sleep(reconnect_timeout)

