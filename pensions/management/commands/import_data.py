import csv
from itertools import islice
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from pensions.models import Benefit, PensionFund


class Command(BaseCommand):
    help = 'Imports individual benefits for the given data year'

    def add_arguments(self, parser):
        parser.add_argument('data_year')

    @transaction.atomic
    def handle(self, *args, **options):
        self.fund_cache = {}

        infile = 'pensions_{}.csv'.format(options['data_year'])
        filepath = os.path.join(settings.BASE_DIR, 'data', 'finished', infile)

        n_deleted, _ = Benefit.objects.filter(data_year=options['data_year']).delete()
        self.stdout.write('deleted {} benefit objects'.format(n_deleted))

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            objects = self._build_generator(reader)
            count = 0
            batch_size = 10000
            while True:
                batch = list(islice(objects, batch_size))
                if not batch:
                    break
                try:
                    Benefit.objects.bulk_create(batch, batch_size)
                except:
                    raise

                count += batch_size
                self.stdout.write('inserted {}'.format(count))

    def _build_generator(self, reader):
        for row in reader:
            fund_key = row['fund']

            try:
                fund = self.fund_cache[fund_key]
            except KeyError:
                fund, _ = PensionFund.objects.get_or_create(name=fund_key)
                self.fund_cache[fund_key] = fund

            row['fund'] = fund

            for field in ('years_of_service', 'final_salary', 'start_date'):
                if row[field] == '':
                    row[field] = None

            yield Benefit(**row)
