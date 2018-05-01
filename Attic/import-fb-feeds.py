import csv
import logging
import pyfaceb

from django.core.exceptions import ObjectDoesNotExist
from parliament.models import *
from eduskunta.member import fix_mp_name
from social.utils import FeedUpdater, UpdateError
from social.models import BrokenFeed

def parse_fb_feed(feed_str):
    fb_feed = feed_str.strip()
    if not fb_feed:
        return
    if fb_feed == '-' or not '/' in fb_feed:
        return
    elif '?' in fb_feed:
        fb_feed = fb_feed.split('?')[0]
    if not fb_feed:
        return

    # Take the last component in the path
    fb_feed = fb_feed.strip('/').split('/')[-1]
    if 'facebook.com' in fb_feed or 'profile.php' in fb_feed or \
            'index.php' in fb_feed:
        return
    elif '(' in fb_feed or ' ' in fb_feed:
        return
    elif fb_feed == 'info':
        return

    return fb_feed

class FeedImporter(object):
    def validate_fb_feed(self, feed_cls, member, feed_name):
        import pyfaceb
        from social.models import BrokenFeed

        person_name = str(member).encode('utf8')
        feed_name = str(feed_name).encode('utf8')
        self.logger.debug("%s: Validating FB feed %s" % (person_name, feed_name))

        # Attempt to find the feed with different parameters
        search_args = [
            {'origin_id__iexact': feed_name},
            {'account_name__iexact': feed_name}
        ]

        cf = None
        for args in search_args:
            try:
                cf = feed_cls.objects.get(type='FB', **args)
                self.logger.debug("%s: Feed %s found" % (person_name, feed_name))
                if cf.member != member:
                    other_name = str(cf.member).encode('utf8')
                    self.logger.warning("%s: Found FB feed (%s) was for %s" %
                        (person_name, feed_name, other_name))
                if not self.replace:
                    return
                break
            except feed_cls.DoesNotExist:
                pass

        # Check if the feed was previously marked broken.
        bf = None
        if not cf:
            try:
                bf = BrokenFeed.objects.get(type='FB', origin_id=feed_name)
                self.logger.debug("%s: FB feed %s marked broken" % (person_name, feed_name))
                if not self.replace:
                    return
            except BrokenFeed.DoesNotExist:
                pass

        # Attempt to download data from FB and mark the feed
        # as broken if we encounter trouble.
        try:
            graph = self.feed_updater.fb_graph.get(feed_name)
        except pyfaceb.exceptions.FBHTTPException as e:
            if not cf and not bf:
                bf = BrokenFeed(type='FB', origin_id=feed_name)
                bf.reason = e.message[0:49]
                bf.save()
            return
        if not 'category' in graph:
            self.logger.warning('%s: FB %s: not a page' % (person_name, feed_name))
            assert not cf
            if not bf:
                bf = BrokenFeed(type='FB', origin_id=feed_name)
                bf.reason = "not-page"
                bf.save()
            return

        # Now we know the feed is valid. If a BrokenFeed object exists,
        # remove it.
        if bf:
            bf.delete()

        origin_id = str(graph['id'])
        if not cf:
            try:
                cf = feed_cls.objects.get(type='FB', origin_id=origin_id)
                if cf.member != member:
                    self.logger.error("FB feed (id %s) was for %s, not %s" % (origin_id, cf.member, member))
                assert cf.member == member
            except feed_cls.DoesNotExist:
                assert feed_cls.objects.filter(member=member, type='FB').count() == 0
                cf = feed_cls(member=member, type='FB')
                self.logger.info("%s: adding FB feed %s" % (person_name, origin_id.encode('utf8')))

        cf.origin_id = origin_id
        cf.account_name = graph.get('username', None)
        cf.save()

    def mark_broken(self, feed_type, feed_id, reason):
        self.logger.warning("Marking %s feed %s as broken (%s)" % (feed_type, feed_id, reason))
        args = {'type': feed_type, 'origin_id': feed_id}
        bf, created = BrokenFeed.objects.get_or_create(**args)
        bf.reason = reason
        bf.save()

    def validate_twitter_feed(self, feed_cls, member, feed_name):
        from social.models import BrokenFeed
        from twython import TwythonError

        person_name = str(member).encode('utf8')
        feed_name = str(feed_name).encode('utf8')
        self.logger.debug("%s: Validating Twitter feed %s" % (person_name, feed_name))

        twitter = self.feed_updater.twitter
        if feed_name.isdigit():
            tw_args = {'user_id': feed_name}
            orm_args = {'origin_id': feed_name}
        else:
            tw_args = {'screen_name': feed_name}
            orm_args = {'account_name__iexact': feed_name}

        try:
            mf = feed_cls.objects.get(type='TW', **orm_args)
            self.logger.debug("%s: Feed %s found" % (person_name, feed_name))
            if mf.member != member:
                other_name = str(mf.member).encode('utf8')
                self.logger.warning("%s: Found TW feed (%s) was for %s" %
                    (person_name, feed_name, other_name))
            if not self.replace:
                return
        except feed_cls.DoesNotExist:
            mf = None
            pass

        # Check if the feed was previously marked broken.
        bf = None
        if not mf:
            try:
                bf = BrokenFeed.objects.get(type='TW', origin_id=feed_name)
                self.logger.debug("%s: TW feed %s marked broken" % (person_name, feed_name))
                if not self.replace:
                    return
            except BrokenFeed.DoesNotExist:
                pass

        try:
            res = twitter.showUser(**tw_args)
        except TwythonError as e:
            self.logger.error('Twitter error: %s', e)
            if e.msg.startswith('Not Found:'):
                self._mark_broken("TW", feed_name, "not-found")
            elif e.msg.startswith('Bad Request:') and 'Rate limit exceeded' in e.msg:
                self.disable_twitter = True
            return
        except ConnectionError as e:
            self.logger.error('Connection error: %s', e)
            return

        origin_id = str(res['id'])
        if not mf:
            feeds = feed_cls.objects.filter(member=member, type='TW')
            if len(feeds):
                self.logger.warning("%s: TW feed already found (screen name '%s')" % (person_name, mf.account_name))
                return
            mf = feed_cls(member=member, type='TW')
            self.logger.info("%s: adding TW feed %s" % (person_name, origin_id))

        mf.origin_id = origin_id
        mf.account_name = res.get('screen_name', None)
        mf.save()


imp = FeedImporter()
imp.logger = logging.getLogger(__name__)
imp.feed_updater = FeedUpdater(imp.logger)
imp.replace = False

reader = csv.reader(open('some-feeds.csv', 'r'), delimiter=',')
for row in reader:
    mp_name = "%s %s" % (row[0].decode('utf8'), row[1].decode('utf8'))
    mp_name = fix_mp_name(mp_name)
    member = Member.objects.get(name=mp_name)
    print("%s: %s" % (mp_name, row[2]))
    if row[2] == 'TW':
        imp.validate_twitter_feed(MemberSocialFeed, member, row[3])
    else:
        imp.validate_fb_feed(MemberSocialFeed, member, row[3])
