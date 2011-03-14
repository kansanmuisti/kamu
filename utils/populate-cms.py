#!/usr/bin/python
# A script to write initial content data into database


import sys
import os
import codecs
#from optparse import OptionParser

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

def process_file(root, filename, category_name, type):
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
        category = category[0]

    if category_name == "news":
        print "Creating newsitem with date %s" % newsdate
        # FIXME add date setting
        item = Newsitem(category=category, date=newsdate)
        item.save()
    else:
        item = Item.objects.filter(category=category)

        if item.count() == 0:
            print "Creating _item_ under category %s" % category_name
            item = Item(category=category)
            item.save()
        else:
            item = item[0]

    content = Content.objects.filter(item=item, language=language)

    if content.count() == 0:
        print "Creating content for item %s with lang %s" % (item, language)
        content = Content(item=item, language=language)
        content.save()
    else:
        return

    f = codecs.open(os.path.join(root, filename), mode="r", encoding="utf8")

    if category_name == "news":
        # Newsfiles contain the subject as first line
        subject = f.readline()[:-1]
    else:
        subject = "Initial commit for %s in %s" % (category, language)

    data = f.read()
    content_data = data
    while data:
        data = f.read()
        content_data += data
    content_data = content_data.strip()

    revision = Revision(content=content, subject=subject, data=content_data, data_markup_type=type)
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
        (category_name, type) = os.path.splitext(filename)
        type = type[1:]

        if type not in allowed_markups:
            print "Ignoring file %s" % filename
            continue

        process_file(root, filename, category_name, type)
