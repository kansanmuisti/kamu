import time
import datetime
import calendar
import email.utils
from twython import Twython

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.conf import settings
from social.models import Feed, Update

class Command(BaseCommand):
    help = "Update social media feeds"

    def process_twitter_timeline(self, twitter, feed):
        self.stdout.write("Processing %s\n" % feed.account_name)
        user_id = feed.origin_id
        args = {'user_id': user_id, 'username': user_id, 'count': 100,
                'trim_user': True}
        tw_list = []
        while True:
            tweets = twitter.getUserTimeline(**args)
            if 'error' in tweets:
                self.stderr.write("\tERROR: %s\n" % tweets['error'])
                if not 'Rate limit exceeded' in tweets['error']:
                    feed.update_error_count += 1
                    feed.save()
                return
            if not len(tweets):
                break
            for tw in tweets:
                try:
                    mp_tw = Update.objects.get(feed=feed, origin_id=tw['id'])
                except Update.DoesNotExist:
                    tw_list.insert(0, tw)
                else:
                    break
            else:
                args['max_id'] = tw_list[0]['id'] - 1
                continue
            break
        self.stdout.write("\tNew tweets: %d\n" % len(tw_list))
        for tw in tw_list:
            mp_tw = Update(feed=feed)
            mp_tw.origin_id = tw['id']
            text = tw['text']
            mp_tw.text = text.replace('&gt;', '>').replace('&lt;', '<')
            date = calendar.timegm(email.utils.parsedate(tw['created_at']))
            mp_tw.created_time = datetime.datetime.fromtimestamp(date)
            try:
                mp_tw.save()
            except:
                self.stderr.write("%s\n" % str(tw))
                raise
        feed.last_update = datetime.datetime.now()
        feed.save()

    def update_twitter(self):
        feed_list = Feed.objects.filter(type='TW')
        # check only feeds that haven't been updated for two hours
        update_dt = datetime.datetime.now() - datetime.timedelta(hours=2)
        feed_list = feed_list.filter(Q(last_update__lt=update_dt) | Q(last_update__isnull=True))
        tw_args = {}
        twitter = Twython(**tw_args)
        for feed in feed_list:
            self.process_twitter_timeline(twitter, feed)


    def handle(self, *args, **options):
        self.update_twitter()
