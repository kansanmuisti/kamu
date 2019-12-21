#!/usr/bin/env python

import sys
import pickle
from twython import Twython

from django.core.management import setup_environ
sys.path.append('.')
import settings
setup_environ(settings)

from parliament.models import Member, MemberSocialFeed

PICKLE_FILE="mp-twitter.pickle"


twitter = Twython()

def read_twitter_lists():
    twitter_lists = ((24404831, 6970755), (17680567, 3656966))
    mps = {}

    for tw_li in twitter_lists:
        args = dict(list_id=tw_li[1], owner_id=tw_li[0], username=tw_li[0],
                    skip_status=True)
        while True:
            results = twitter.getListMembers(**args)
            users = results['users']
            for user in users:
                if user['id'] not in mps:
                    mps[user['id']] = user
                print("%s:%s" % (user['name'], user['id']))
            cursor = results['next_cursor']
            if not cursor:
                break
            args['cursor'] = cursor
    return mps

try:
    f = open(PICKLE_FILE, 'r')
    tw_mps = pickle.load(f)
except IOError:
    tw_mps = read_twitter_lists()
    f = open(PICKLE_FILE, 'w')
    pickle.dump(tw_mps, f)

f.close()

MP_TRANSFORM = {
    "veltto virtanen": "Pertti Virtanen",
    "n. johanna sumuvuori": "Johanna Sumuvuori",
    "eeva-johanna elorant": "Eeva-Johanna Eloranta",
    "outi alanko-kahiluot": "Outi Alanko-Kahiluoto",
}

print("%d Twitter feeds found" % len(list(tw_mps.keys())))

mp_list = list(Member.objects.all())

for (tw_id, tw_info) in list(tw_mps.items()):
    for mp in mp_list:
        name = tw_info['name'].lower()
        if name in MP_TRANSFORM:
            name = MP_TRANSFORM[name].lower()
        if mp.get_print_name().lower() == name.lower():
            break
    else:
        print("%s: no match" % tw_info['name'])
        continue
    try:
        feed = MemberSocialFeed.objects.get(member=mp, type='TW', origin_id=tw_id)
    except MemberSocialFeed.DoesNotExist:
        feed = MemberSocialFeed(member=mp, type='TW', origin_id=tw_id)
    feed.account_name = tw_info['screen_name']
    feed.save()
