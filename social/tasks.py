from celery.task import PeriodicTask
from datetime import timedelta

from social.utils import FeedUpdater, UpdateError

class UpdateFeedsTask(PeriodicTask):
    run_every = timedelta(minutes=15)

    def run(self, **kwargs):
        logger = self.get_logger()
        updater = FeedUpdater(logger)
        print "Updating feeds"
        updater.update_feeds()
        print "Feed update done"
