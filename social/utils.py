import urlparse
import pprint
import requests
import logging
import datetime
import email.utils
import urllib
import calendar
import time
from twython import Twython, TwythonError
import pyfaceb
import dateutil.parser
import dateutil.tz

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from social.models import ApiToken, Feed, Update

class UpdateError(Exception):
    def __init__(self, msg, can_continue=False, feed_ok=False):
        self.can_continue = can_continue
        self.feed_ok = feed_ok
        super(UpdateError, self).__init__(msg)

TOKEN_URL = "https://graph.facebook.com/oauth/access_token?" + \
        "client_id=%s&client_secret=%s&grant_type=client_credentials"

def get_facebook_token():
    try:
        token = ApiToken.objects.get(type='FB')
        return token.token
    except ApiToken.DoesNotExist:
        pass

    r = requests.get(TOKEN_URL % (settings.FACEBOOK_APP_ID, settings.FACEBOOK_API_SECRET))
    arr = r.text.split('=')
    if arr[0] != 'access_token':
        raise Exception("FB returned invalid access token")
    ApiToken.objects.filter(type='FB').delete()
    token = ApiToken(type='FB', token=arr[1])
    token.save()
    return token.token

TWITTER_SETTING_MAP = {
    'TWITTER_CONSUMER_KEY': 'app_key',
    'TWITTER_CONSUMER_SECRET': 'app_secret',
    'TWITTER_ACCESS_TOKEN': 'oauth_token',
    'TWITTER_ACCESS_TOKEN_SECRET': 'oauth_token_secret'
}

def _append_without_dupes(feed_list, feed_list_b):
    feed_dict = {}
    for f in feed_list:
        feed_dict[f.pk] = f
    for f in feed_list_b:
        if f.pk not in feed_dict:
            feed_list.append(f)

class FeedUpdater(object):
    def __init__(self, logger=None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger
        token = get_facebook_token()
        self.fb_graph = pyfaceb.FBGraph(token)

        tw_args = {}
        for key in TWITTER_SETTING_MAP.keys():
            val = getattr(settings, key, None)
            if not val:
                tw_args = {}
                break
            tw_args[TWITTER_SETTING_MAP[key]] = val

        twitter = Twython(**tw_args)
        self.twitter = twitter

    def _get_field_max_len(self, obj, field_name):
        max_length = obj.__class__._meta.get_field(field_name).max_length
        return max_length

    def _set_field_with_len(self, update, field_name, text):
        max_length = self._get_field_max_len(update, field_name)
        if text and len(text) > max_length:
            self.logger.warning("Truncating feed %s update %s field '%s' (length %d)" % (
                update.feed.origin_id, update.origin_id, field_name, len(text)))
            text = text[0:max_length-3]
            text += "..."
        setattr(update, field_name, text)

    def subscribe_to_twitter_list(self, base_name, feeds):
        owner_name = getattr(settings, 'TWITTER_SCREEN_NAME')
        user_ids = [feed.origin_id for feed in feeds]
        list_idx = 1
        already_subscribed = []
        while True:
            list_slug = "%s-%d" % (base_name, list_idx)
            args = dict(owner_screen_name=owner_name, slug=list_slug)
            try:
                list_members = self.twitter.getListMembers(**args)
            except TwythonError as e:
                if 'Not Found' in e.msg:
                    break

    def find_feeds_to_update(self, feed_type=None):
        counts = []

        base_query = Feed.objects.order_by('last_update')
        if feed_type:
            base_query = base_query.filter(type=feed_type)
        # Check first feeds that have never been updated.
        feed_list = list(base_query.filter(Q(last_update__isnull=True)))
        counts.append(len(feed_list))

        # Then feeds that haven't been updated in two days.
        update_dt = datetime.datetime.now() - datetime.timedelta(days=2)
        fl = list(base_query.filter(last_update__lt=update_dt))
        counts.append(len(fl))
        _append_without_dupes(feed_list, fl)

        # Finally feeds that haven't been updated in two hours,
        # but that are active (i.e. have posts dating from the
        # last week).
        # In the case of Twitter, we're using live streaming,
        # so skip this.
        if feed_type != 'TW':
            update_dt = datetime.datetime.now() - datetime.timedelta(hours=2)
            post_dt = datetime.datetime.now() - datetime.timedelta(days=3)
            active = Q(update__created_time__gt=post_dt)
            fl = list(base_query.filter(Q(last_update__lt=update_dt) & active).distinct())
        else:
            fl = []
        counts.append(len(fl))
        _append_without_dupes(feed_list, fl)

        counts.append(len(feed_list))
        self.logger.info("updating a total of %d feeds (%d never, %d old, %d active)" % (
                counts[3], counts[0], counts[1], counts[2]))

        return feed_list

    @transaction.commit_on_success
    def process_tweet(self, tweet):
        self.logger.debug("incoming tweet with id %s" % tweet['id'])
        try:
            tw_obj = Update.objects.get(feed__type="TW", origin_id=tweet['id'])
            return
        except Update.DoesNotExist:
            pass
        tw_user = tweet['user']
        try:
            feed = Feed.objects.get(type="TW", origin_id=tw_user['id'])
        except Feed.DoesNotExist:
            self.logger.debug("feed %s (%s) not found" % (tw_user['id'], tw_user['screen_name']))
            return
        self.logger.debug("tweet for feed %s" % unicode(feed))
        feed.last_update = datetime.datetime.now()
        feed.interest = tw_user['followers_count']
        feed.picture = tw_user['profile_image_url']
        feed.account_name = tw_user['screen_name']
        feed.save()
        tw_obj = Update(feed=feed, origin_id=tweet['id'])
        text = tweet['text']
        tw_obj.text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&#39;', "'")
        date = calendar.timegm(email.utils.parsedate(tweet['created_at']))
        tw_obj.created_time = datetime.datetime.fromtimestamp(date)
        try:
            tw_obj.save()
        except Exception as e:
            self.logger.error(str(e))
            raise

    @transaction.commit_on_success
    def process_twitter_feed(self, feed):
        self.logger.info("Processing Twitter feed %s" % feed.account_name)
        user_id = feed.origin_id
        args = {'user_id': user_id, 'username': user_id, 'count': 200,
                'trim_user': True}
        tw_list = []
        try:
            info = self.twitter.showUser(**args)
        except TwythonError as e:
            if 'Unauthorized:' in e.msg:
                raise UpdateError(e.msg, can_continue=True)
            self.logger.error("Got Twitter exception: %s" % e)
            if "Rate limit exceeded" in e.msg:
                raise UpdateError("Rate limit exceeded", can_continue=False, feed_ok=True)
            raise UpdateError(e.msg)
        feed.interest = info['followers_count']
        feed.picture = info['profile_image_url']
        feed.account_name = info['screen_name']
        while True:
            # retry two times if the twitter call fails
            for i in range(3):
                try:
                    tweets = self.twitter.getUserTimeline(**args)
                except ValueError:
                    if i == 2:
                        raise
                    self.logger.warning("Got exception, retrying.")
                    continue
                except TwythonError as e:
                    self.logger.error("Got Twitter exception: %s" % e)
                    if 'Unauthorized:' in e.msg:
                        raise UpdateError(e.msg, can_continue=True)
                    if "Rate limit exceeded" in e.msg:
                        raise UpdateError("Rate limit exceeded", can_continue=False, feed_ok=True)
                    raise UpdateError(e.msg)
                break
            if 'error' in tweets:
                self.logger.error("%s" % tweets['error'])
                if not 'Rate limit exceeded' in tweets['error']:
                    self.logger.error("Twitter error: %s" % tweets['error'])
                    raise UpdateError(tweets['error'])
                else:
                    self.logger.error("Twitter rate limit exceeded")
                    raise UpdateError(tweets['error'])
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
        self.logger.debug("New tweets: %d" % len(tw_list))
        for tw in tw_list:
            tw_obj = Update(feed=feed)
            tw_obj.origin_id = tw['id']
            text = tw['text']
            tw_obj.text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&#39;', "'")
            date = calendar.timegm(email.utils.parsedate(tw['created_at']))
            tw_obj.created_time = datetime.datetime.fromtimestamp(date)
            try:
                tw_obj.save()
            except Exception as e:
                self.logger.error(str(e))
                raise
        feed.update_error_count = 0
        feed.last_update = datetime.datetime.now()
        feed.save()

    def _fb_get(self, url):
        last_e = None
        # Allow for three retries
        for i in range(0, 3):
            try:
                ret = self.fb_graph.get(url)
                return ret
            except pyfaceb.exceptions.FBHTTPException as e:
                self.logger.error("%s" % e)
                if i < 3:
                    # Some errors seem to be transient.
                    if '#803' in e.message or '2500' in e.message:
                        self.logger.error("Retrying")
                        last_e = e
                        # Sleep for a while before continuing.
                        time.sleep(0.5)
                        continue
                    else:
                        raise UpdateError(e.message)
        # If we got this far, the error repeated 3 times, so
        # we bail out.
        raise UpdateError(last_e.message)

    @transaction.commit_on_success
    def process_facebook_feed(self, feed, full_update=False):
        self.logger.info('Processing feed %s' % unicode(feed))

        # First update the feed itself
        url = '%s&fields=picture,likes,about' % feed.origin_id
        feed_info = self._fb_get(url)
        feed.picture = feed_info.get('picture', {}).get('data', {}).get('url', None)
        feed.interest = feed_info.get('likes', None)
        # Limit downloading of personal feeds to last two months.
        if 'category' not in feed_info:
            feed.is_personal = True
            since = datetime.datetime.now() - datetime.timedelta(weeks=2*4)
            since = int(time.mktime(since.timetuple()))
            filter_args = "&since=%d" % since
            self.logger.debug('%s is a personal feed' % unicode(feed))
        else:
            feed.is_personal = False
            filter_args = ""

        if full_update:
            count = 100
        else:
            count = 20
        new_count = 0
        url = '%s/posts&limit=%d%s' % (feed.origin_id, count, filter_args)
        while True:
            self.logger.info('Fetching %s' % url)
            g = self._fb_get(url)
            found = False
            for post in g['data']:
                # Sanity check
                assert post['from']['id'] == feed.origin_id
                if post['type'] in ('question', 'swf', 'music', 'offer'):
                    # We skip these updates for now.
                    continue
                if post['type'] == 'status' and 'message' not in post:
                    # We're not interested in status updates with no content.
                    continue
                try:
                    upd = Update.objects.get(feed=feed, origin_id=post['id'])
                    found = True
                    if not full_update:
                        continue
                except Update.DoesNotExist:
                    upd = Update(feed=feed, origin_id=post['id'])
                    created = True
                    new_count += 1

                utc = dateutil.parser.parse(post['created_time'])
                upd.created_time = utc.astimezone(dateutil.tz.tzlocal())
                self._set_field_with_len(upd, 'text', post.get('message', None))
                upd.share_link = post.get('link', None)
                upd.picture = post.get('picture', None)
                self._set_field_with_len(upd, 'share_title', post.get('name', None))
                self._set_field_with_len(upd, 'share_caption', post.get('caption', None))
                self._set_field_with_len(upd, 'share_description', post.get('description', None))
                if upd.picture and len(upd.picture) > self._get_field_max_len(upd, 'picture'):
                    self.logger.warning("%s: Removing too long (%d) picture link" % (upd.origin_id, len(upd.picture)))
                    upd.picture = None
                if upd.share_link and len(upd.share_link) > self._get_field_max_len(upd, 'share_link'):
                    self.logger.warning("%s: Removing too long (%d) link" % (upd.origin_id, len(upd.share_link)))
                    upd.share_link = None
                sub_type = post.get('status_type', None)
                if sub_type:
                    upd.sub_type = sub_type
                else:
                    upd.sub_type = None
                upd.interest = post.get('likes', {}).get('count', None)
                if post['type'] == 'link':
                    upd.type = 'link'
                    if not upd.share_link:
                        self.logger.warning("FB %s: No link given for 'link' update" % post['id'])
                elif post['type'] == 'photo':
                    upd.type = 'photo'
                    assert upd.share_link
                    assert upd.picture
                elif post['type'] == 'status':
                    upd.type = 'status'
                elif post['type'] == 'video':
                    upd.type = 'video'
                    if not upd.share_link:
                        # Fall back to the 'source' attribute
                        upd.share_link = post.get('source', None)
                        if not upd.share_link:
                            pprint.pprint(post)
                            raise Exception("%s: No link for 'video 'update" % post['id'])
                        if upd.share_link and len(upd.share_link) > self._get_field_max_len(upd, 'share_link'):
                            self.logger.warning("%s: Removing too long link" % upd.origin_id)
                            upd.share_link = None
                else:
                    pprint.pprint(post)
                    raise Exception("Unknown FB update type: %s" % post['type'])
                upd.save()

            if not 'paging' in g:
                break
            next_args = urlparse.parse_qs(urlparse.urlparse(g['paging']['next']).query)
            until = int(next_args['until'][0])
            # If we didn't have any of the updates, get a bigger batch next
            # time.
            if not found:
                count = 100
            elif not full_update:
                # If at least some of the updates were in our DB already,
                # the feed is up-to-date.
                break
            url = "%s/posts&limit=%d&until=%d%s" % (feed.origin_id, count, until, filter_args)
        self.logger.info("%s: %d new updates" % (feed.account_name, new_count))
        feed.update_error_count = 0
        feed.last_update = datetime.datetime.now()
        feed.save()

    def process_feed(self, feed):
        if feed.type == "TW":
            return self.process_twitter_feed(feed)
        assert feed.type == "FB"
        return self.process_facebook_feed(feed)

    def update_feeds(self):
        feed_types = ("TW", "FB")
        for ft in feed_types:
            feed_list = self.find_feeds_to_update(ft)
            for feed in feed_list:
                try:
                    self.process_feed(feed)
                except UpdateError as e:
                    if not e.feed_ok:
                        feed.update_error_count += 1
                        feed.last_update = datetime.datetime.now()
                        feed.save()
                    if not e.can_continue:
                        break

def get_facebook_graph(graph_id):
    token = get_facebook_token()
    fbg = pyfaceb.FBGraph(token)
    return fbg.get(graph_id)
