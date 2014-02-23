import os
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...party import PartyImporter
from ...member import MemberImporter
from ...minutes import MinutesImporter
from ...vote import VoteImporter
from ...seat import SeatImporter
from ...funding import FundingImporter
from ...doc import DocImporter
from utils.http import HttpFetcher

class Command(BaseCommand):
    help = 'Import data from the Finnish parliament'
    option_list = BaseCommand.option_list + (
        make_option('--party', action='store_true', dest='party',
                    default=False, help='Import parties'),
        make_option('--member', action='store_true', dest='member',
                    default=False, help='Import MPs'),
        make_option('--seat', action='store_true', dest='seat',
                    default=False, help='Import MP seatings'),
        make_option('--minutes', action='store_true', dest='minutes',
                    default=False, help='Import plenary session minutes'),
        make_option('--doc', action='store_true', dest='docs',
                    default=False, help='Import parliament documents'),
        make_option('--vote', action='store_true', dest='vote',
                    default=False, help='Import plenary session votes'),
        make_option('--funding', action='store_true', dest='funding',
                    default=False, help='Import election funding'),
        make_option('--single', metavar='ID', dest='single', help='Import only a single element'),
        make_option('--from-year', metavar='YEAR', dest='from_year', help='Start importing from YEAR'),
        make_option('--from-id', metavar='ID', dest='from_id', help='Start importing from ID'),
        make_option('--replace', action='store_true', dest='replace',
                    default=False, help='Replace values of existing objects'),
        make_option('--full', action='store_true', dest='full',
                    default=False, help='Perform a full update'),
        make_option('--cache', action='store', dest='cache',
                    help='Use cache in supplied director'),
        make_option('--dry-run', action='store_true', dest='dry_run',
                    help='Do not commit any changes to the database')
    )

    def handle(self, *args, **options):
        http = HttpFetcher()
        if options['cache']:
            http.set_cache_dir(options['cache'])
        min_importer = MinutesImporter(http_fetcher=http)
        min_importer.replace = options['replace']
        min_importer.import_terms()

        if options['party']:
            importer = PartyImporter(http_fetcher=http)
            importer.replace = options['replace']
            importer.import_parties()
            importer.import_governments()
            importer.import_governingparties()
        if options['member']:
            importer = MemberImporter(http_fetcher=http)
            importer.replace = options['replace']
            importer.import_districts()
            args = {}
            if options['single']:
                args['single'] = options['single']
            args['full'] = options['full']
            args['dry_run'] = options['dry_run']
            importer.import_members(**args)
        if options['seat']:
            importer = SeatImporter(http_fetcher=http)
            importer.replace = options['replace']
            importer.import_seats()
        if options['minutes']:
            args = {}
            if options['single']:
                args['single'] = options['single']
            if options['from_year']:
                args['from_year'] = options['from_year']
            if options['from_id']:
                args['from_id'] = options['from_id']
            args['full'] = options['full']
            min_importer.import_minutes(args)
        if options['docs']:
            importer = DocImporter(http_fetcher=http)
            importer.replace = options['replace']
            args = {}
            if options['single']:
                args['single'] = options['single']
            if options['from_year']:
                args['from_year'] = options['from_year']
            args['full'] = options['full']
            importer.import_docs(**args)
        if options['vote']:
            importer = VoteImporter(http_fetcher=http)
            importer.replace = options['replace']
            args = {}
            if options['single']:
                args['single'] = options['single']
            if options['from_year']:
                args['from_year'] = options['from_year']
            args['full'] = options['full']
            importer.import_votes(**args)
        if options['funding']:
            importer = FundingImporter(http_fetcher=http)
            importer.replace = options['replace']
            importer.import_funding()
