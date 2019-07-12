import csv
from itertools import islice
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from pensions.models import Benefit, PensionFund


class Command(BaseCommand):
    help = 'Imports individual benefits for the given data year'

    NULL_FIELDS = (
        'years_of_service',
        'final_salary',
        'start_date',
        'status'
    )

    def add_arguments(self, parser):
        parser.add_argument('data_file',
                            help='Absolute path to individal data file to import')

        parser.add_argument('data_year',
                            help='Data year to which individual data file pertains')

        parser.add_argument('--delete',
                            default='True',
                            help='Whether to delete existing data for the given year.' +
                                 'Set to False if uploading partial data.')

    @transaction.atomic
    def handle(self, *args, **options):
        self.fund_cache = {}

        data_year = options['data_year']

        if options['delete'] == 'True':
            n_deleted, _ = Benefit.objects.filter(data_year=data_year).delete()
            self.stdout.write('deleted {0} existing Benefit objects from {1}'.format(n_deleted, data_year))

        filepath = options['data_file']

        self.stdout.write('importing Benefits from {0}'.format(filepath))

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            objects = self._format_row(reader)

            count = 0
            batch_size = 10000

            while True:
                batch = list(islice(objects, batch_size))

                if not batch:
                    break

                Benefit.objects.bulk_create(batch, batch_size)

                count += batch_size

                self.stdout.write('inserted {0} Benefit objects'.format(count))

    def _format_row(self, reader):
        for row in reader:
            row['fund'] = self._hydrate_fund(row['fund'])
            row = self._cast_to_none(row)
            yield Benefit(**row)

    def _hydrate_fund(self, fund_key):
        try:
            fund = self.fund_cache[fund_key]

        except KeyError:
            try:
                fund = PensionFund.objects.get(name=fund_key)

            except PensionFund.DoesNotExist:
                existing_funds = ', '.join([fund.name for fund in PensionFund.objects.all()])
                message = 'Fund name {} does not exist. Existing funds are: {}'.format(fund_key, existing_funds)
                raise ValueError(message)

            else:
                self.fund_cache[fund_key] = fund

        return fund

    def _cast_to_none(self, row):
        for field in self.NULL_FIELDS:
            if row[field] == '':
                row[field] = None

        return row
