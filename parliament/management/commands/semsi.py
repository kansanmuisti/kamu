from __future__ import absolute_import

import os
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.conf import settings
from parliament.models import Document
from datetime import datetime, timedelta

import requests

class Command(BaseCommand):
    help = 'Index parliament documents for semsi'
    option_list = BaseCommand.option_list + (
        make_option('--rebuild', action='store_true', dest='rebuild',
                    help='Rebuild index (full refresh)'),
        make_option('--all', action='store_true', dest='all',
                    help='Index all documents'),
        make_option('--age', action='store', dest='age', type='int', default=2,
                    help='Index documents older than AGE hours'),
        make_option('--single', action='store', dest='single', type='string',
                    help='Index only the given document')
    )

    def get_index_url(self):
        return self.semsi_url + "index/" + self.index_name
    def get_doc_url(self):
        return self.get_index_url() + "/doc"

    def send_doc(self, doc, index=True):
        if not doc.summary:
            return
        url = "http://%s%s" % (self.site.domain, doc.get_absolute_url())
        data = {'title': doc.subject, 'id': doc.url_name, 'text': doc.summary, 'url': url}
        if index:
            data['index'] = True
        r = self.session.post(self.get_doc_url(), data=json.dumps(data), headers=self.headers)
        if r.status_code != 200:
            raise Exception("Sending document failed with %d: %s" % (r.status_code, r.content))

    def handle(self, *args, **options):
        self.semsi_url = settings.SEMSI_URL
        self.index_name = 'kamu'

        self.session = requests.Session()

        if options['rebuild']:
            if options['single']:
                print "You can't give both 'rebuild' and 'single' options."
                exit(1)
            print "Deleting index..."
            self.session.delete(self.get_index_url())
            docs = Document.objects.all()
        elif options['age']:
            age = options['age']
            ts = datetime.now() - timedelta(hours=age)
            docs = Document.objects.filter(update_time__gte=ts)

        self.headers = {'Content-Type': 'application/json'}

        count = docs.count()
        self.site = Site.objects.all()[0]

        if options['single']:
            doc = Document.objects.get(url_name=options['single'])
            self.send_doc(doc, index=True)
            docs = []

        index = not options['rebuild']
        for idx, doc in enumerate(docs):
            self.send_doc(doc, index=index)
            if idx % 100 == 99:
                print "%d of %d documents sent" % (idx + 1, count) 

        if options['rebuild']:
            data = {'train': True}
            print "Training..."
            r = self.session.post(self.get_index_url(), data=json.dumps(data), headers=headers)
            if r.status_code != 200:
                raise Exception("Train failed with %d: %s" % (r.status_code, r.content))
                exit(1)
        else:
            print "Indexing..."
            r = self.session.post(self.get_index_url(), data={})
            if r.status_code != 200:
                raise Exception("Index failed with %d: %s" % (r.status_code, r.content))
        print "All done."
