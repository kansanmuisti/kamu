import time
import datetime
import calendar
import email.utils
from twython import Twython

from django.core.management.base import BaseCommand, CommandError
from votes.models import Member, MemberTweet

class Command(BaseCommand):
    help = "Update MP social media feeds"

    def process_timeline(self, twitter, mp):
        user_id = mp.twitter_account
        args = {'user_id': user_id, 'username': user_id, 'count': 100,
                'trim_user': True}
        tw_list = []
        while True:
            self.stdout.write("%s (%d fetched)\n" % (mp, len(tw_list)))
            tweets = twitter.getUserTimeline(**args)
            if not len(tweets):
                break
            for tw in tweets:
                try:
                    mp_tw = MemberTweet.objects.get(tweet_id=tw['id'])
                except MemberTweet.DoesNotExist:
                    tw_list.insert(0, tw)
                else:
                    break
            else:
                args['max_id'] = tw_list[0]['id'] - 1
                continue
            break

        for tw in tw_list:
            mp_tw = MemberTweet(member=mp)
            mp_tw.tweet_id = tw['id']
            mp_tw.user_id = tw['user']['id']
            text = tw['text']
            mp_tw.text = text.replace('&gt;', '>').replace('&lt;', '<')
            date = calendar.timegm(email.utils.parsedate(tw['created_at']))
            mp_tw.created_at = datetime.datetime.fromtimestamp(date)
            try:
                mp_tw.save()
            except:
                print tw
                print vars(mp_tw)
                raise

    def update_twitter(self):
        mp_list = Member.objects.filter(twitter_account__isnull=False)
        twitter = Twython()
        for mp in mp_list[1:2]:
            self.process_timeline(twitter, mp)


    def handle(self, *args, **options):
        self.update_twitter()
