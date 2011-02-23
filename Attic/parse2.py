#!/usr/bin/python

import os
import sys
import urllib2
import pprint
import feedparser
from BeautifulSoup import BeautifulSoup
from lxml import etree, html

sys.path.append('../devel')
sys.path.append('../devel/kamu')
from kamu import settings
from django.core.management import setup_environ
setup_environ(settings)

from django.contrib.sites.models import Site
from kamu.votes.models import Member
from kamu.lifestream.models import Lifestream, Feed, Item

#Item.objects.all().delete()
#Feed.objects.all().delete()

PATH = 'm2/'

def get_feed_link(url):
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    try:
        f = opener.open(url)
    except urllib2.HTTPError:
        return None
    except urllib2.URLError:
        return None
    s = f.read()
    f.close()

    html_doc = html.fromstring(s)
    html_doc.make_links_absolute(url)
    content = html_doc.xpath('.//link')
    atom_link = rss_link = None
    for a in content:
        if not 'type' in a.attrib:
            continue
        if ('type' in a.attrib) and a.attrib['type'].lower() == 'text/css':
            continue
        feed_link = None
        t = a.attrib['type'].lower()
        if t == 'application/atom+xml' and not atom_link:
            atom_link = a.attrib['href']
        elif t == 'application/rss+xml' and not rss_link:
            rss_link = a.attrib['href']
    # Prefer Atom link over RSS.
    feed_link = None
    if atom_link:
        feed_link = atom_link
    elif rss_link:
        feed_link = rss_link
    return feed_link

f_list = os.listdir(PATH)
for f_name in f_list:
    f = open(PATH + f_name)
    s = f.read()
    f.close()

    html_doc = html.fromstring(s)
    name = html_doc.xpath(".//div[@id='profile']/h2")[0].text
    print "%3d. %3s: %s" % (f_list.index(f_name), f_name, name)

    links = html_doc.xpath(".//div[@class='col col2']//a[starts-with(@href,'http://')]")
    twit_user = blog_link = None
    for l in links:
        url = l.attrib['href']
        if url.startswith('http://twitter.com'):
            if twit_user:
                continue
            arr = url.split('/')
            if arr[4] != 'statuses':
                raise Exception()
            twit_user = arr[3]
        elif not blog_link:
            blog_link = url

    member = Member.objects.get(name=name)
    ls = Lifestream.objects.for_object(member)
    if not ls:
        ls = Lifestream(content_object=member)
        ls.site = Site.objects.get_current()
        ls.title = member.get_print_name()
        ls.slug = member.url_name
        ls.save()
    else:
        # One MP should have at most one.
        ls = ls.get()

    feed_list = Feed.objects.filter(lifestream=ls)

    if twit_user:
        print "\tTwitter: %s" % twit_user
        if not member.twitter_account:
            member.twitter_account = twit_user
            member.save()
    if blog_link:
        print "\tBlog: %s" % blog_link

    if twit_user and not feed_list.filter(domain='twitter'):
        print "\tNew Twitter!"
        twit_link = get_feed_link('http://twitter.com/%s' % twit_user)
        if not twit_link:
            raise Exception("Twitter RSS feed not found!")
        feed = Feed(lifestream=ls, domain='twitter')
        feed.url = twit_link
        feed.name = 'Twitter feed for %s' % member.get_print_name()
        feed.fetchable = True
        feed.plugin = 'lifestream.plugins.twitter.TwitterPlugin'
        feed.save()

    if blog_link and not feed_list.filter(domain='blog'):
        print "\tNew blog!"
        feed_link = get_feed_link(blog_link)
        if not feed_link:
            print "\tBut no RSS feed found!"
            continue
        feed = Feed(lifestream=ls, domain='blog')
        feed.url = feed_link
        feed.name = 'Blog for %s' % member.get_print_name()
        feed.fetchable = True
        if 'vihreablogi' in feed_link:
            feed.plugin_class_name = 'social.feeds.VihreaPlugin'
        feed.save()

    print ""
