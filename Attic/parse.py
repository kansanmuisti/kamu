#!/usr/bin/python

import os
import sys
import urllib.request, urllib.error, urllib.parse
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

PATH = 'm/'

f_list = os.listdir(PATH)
for f_name in f_list:
    f = open(PATH + f_name)
    s = f.read()
    f.close()
    soup = BeautifulSoup(s)
    elem_list = soup.findAll('div', {"class": "seeother"})
    print("%3d. %s" % (f_list.index(f_name), f_name))
    elem = elem_list[0].find('a')
    if elem.contents[0] != 'Wikipedia':
        raise Exception()
    wiki_link = elem['href']
    elem = soup.find('a', {'class': 'item_url'})
    blog_link = elem['href']

    name = urllib.parse.unquote(f_name).replace('_', ' ')
    member = Member.objects.get_with_print_name(name)

    print(blog_link)

    opener = urllib.request.build_opener(urllib.request.HTTPHandler)
    try:
        f = opener.open(blog_link)
    except urllib.error.HTTPError:
        continue
    except urllib.error.URLError:
        continue
    s = f.read()
    f.close()

    html_doc = html.fromstring(s)
    html_doc.make_links_absolute(blog_link)
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

    if feed_link:
        d = feedparser.parse(feed_link)
        try:
            ls = Lifestream.objects.for_object(member).get()
        except Lifestream.DoesNotExist:
            ls = Lifestream(content_object=member)
            ls.site = Site.objects.get_current()
            ls.title = member.get_print_name()
            ls.slug = member.url_name
            ls.save()
        try:
            feed = Feed.objects.get(lifestream=ls, domain='blog')
        except Feed.DoesNotExist:
            feed = Feed(lifestream=ls, domain='blog')
            feed.url = feed_link
            feed.name = 'Blog for %s' % member.get_print_name()
            feed.fetchable = True
            if 'vihreablogi' in feed_link:
                feed.plugin_class_name = 'social.feeds.VihreaPlugin'
            feed.save()

    print("")
