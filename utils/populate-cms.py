#!/usr/bin/python
# A script to write initial content data into database


import sys
import os
import codecs
from datetime import datetime

from django.core.management import setup_environ

my_path = os.path.abspath(os.path.dirname(__file__))
kamu_path = os.path.normpath(my_path + '/..')
# Change this if you have your initial content elsewhere
content_path = os.path.normpath(my_path + '/../Content/cms')

sys.path.insert(1, kamu_path)
sys.path.insert(2, os.path.normpath(kamu_path + '/..'))

allowed_markups = ['html', 'markdown']

from kamu import settings

setup_environ(settings)
from django.db import connection, transaction
from django import db

from kamu.cms.models import Category, Newsitem, Item, Content, Revision

def process_file(root, filename, category_name, mu_type):
    print "Processing file %s" % os.path.join(root, filename)

    #Special case for newsitems
    if filename.startswith("news"):
        (category_name, newsdate, order) = filename.split("_")

    category = Category.objects.filter(name=category_name)

    if category.count() == 0:
        print "Creating category %s" % category_name
        category = Category(name=category_name)
        category.save()
    else:
        assert(category.count() == 1)
        category = category[0]

    if category_name == "news":
        print "Processing newsitem with date %s" % newsdate
        item = Newsitem.objects.filter(category=category, date=newsdate)
        # FIXME: Many newsitems per date
        if not item.count():
            item = Newsitem(category=category, date=newsdate)
            item.save()
        else:
            assert(item.count() == 1)
            item = item[0]
    else:
        item = Item.objects.filter(category=category)
        if item.count() == 0:
            print "Creating_item under category %s" % category_name
            item = Item(category=category)
            item.save()
        else:
            item = item[0]

    full_fname = os.path.join(root, filename)

    content = Content.objects.filter(item=item, language=language)
    if content.count() == 0:
        print "Creating content for item %s with lang %s" % (item, language)
        content = Content(item=item, language=language)
        content.save()
    else:
        content = content[0]
        revision = content.get_latest_revision()
        mtime = datetime.fromtimestamp(os.path.getmtime(full_fname))
        if revision and revision.date >= mtime:
            print "\tSkipping based on file mtime"
            return

    f = codecs.open(full_fname, mode="r", encoding="utf8")

    if category_name == "news":
        # Newsfiles contain the subject as first line
        subject = f.readline()[:-1]
        # Summary is defined as being all the text after subject until
        # marker "[full]" alone at the beginning of line with LF at end
        summary = ""
        for line in f:
            if line == "[full]\n":
                break
            summary += line
    else:
        subject = "Initial commit for %s in %s" % (category, language)
        summary = ""

    data = f.read()
    content_data = data
    while data:
        data = f.read()
        content_data += data
    content_data = content_data.strip()

    revision = Revision(content=content, subject=subject, summary=summary,
                        summary_markup_type=mu_type, data=content_data,
                        data_markup_type=mu_type)
    revision.save()
    print "Prepared revision %s" % revision

# FIXME. This loop does not handle ordering of newsitems within
# the same day.
for root, dirs, files in os.walk(content_path):
    if not files:
        continue

    (head,tail) = os.path.split(root)
    language = tail

    for filename in files:
        (category_name, mu_type) = os.path.splitext(filename)
        mu_type = mu_type[1:]

        if mu_type not in allowed_markups:
            print "Ignoring file %s" % filename
            continue

        process_file(root, filename, category_name, mu_type)
