import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...importer import EduskuntaImporter
from utils.http import HttpFetcher

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    help = 'Import data from the Finnish parliament'

    def handle(self, *args, **options):
        http = HttpFetcher()
        http.set_cache_dir(os.path.join(settings.SITE_ROOT, '.cache'))
        importer = EduskuntaImporter(http_fetcher=http)
        importer.fetch_minutes()

