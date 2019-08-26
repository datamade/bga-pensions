from urllib.parse import urlencode

from django.contrib.humanize.templatetags.humanize import intword, intcomma
from django.contrib.auth import logout as log_out
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Q, FloatField, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView

from django_datatables_view.base_datatable_view import BaseDatatableView
from postgres_stats.aggregates import Percentile

from pensions.models import PensionFund, Benefit


CACHE_TIMEOUT = 86400


class Index(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['data_years'] = list(self.data_years)
        context['pension_funds'] = self.pension_funds
        context['data_by_year'] = self.data_by_year()

        return context

    def _format_large_number(self, number):
        word = intword(number)
        try:
            float(word)
        except ValueError:
            return word
        else:
            return intcomma(number)

    def data_by_year(self):
        data_by_year = {}

        data_by_fund = self.fund_metadata
        funding_aggregates = self.funding_aggregates

        for year in self.data_years:
            year_data = {
                'aggregate_funding': funding_aggregates[year],
                'data_by_fund': data_by_fund[year],
            }

            data_by_year[year] = year_data

        return data_by_year

    @property
    def _cache(self):
        if not hasattr(self, '_kache'):
            self._kache = cache.get_many([
                'data_years',
                'benefit_aggregates',
                'binned_benefit_data'
            ])

        return self._kache

    @property
    def data_years(self):
        data = self._cache.get('data_years', [])

        if not data:
            data = Benefit.objects.distinct('data_year')\
                                  .values_list('data_year', flat=True)

            cache.set('data_years', data, CACHE_TIMEOUT)

        return data

    @property
    def pension_funds(self):
        if not hasattr(self, '_pension_funds'):
            self._pension_funds = PensionFund.objects.all()
        return self._pension_funds

    @property
    def benefit_aggregates(self):
        data = self._cache.get('benefit_aggregates', {})

        if not data:
            aggregates = Benefit.objects\
                                .values('fund__name', 'data_year')\
                                .annotate(median=Percentile('amount', 0.5, output_field=FloatField()), count=Count('id'))

            data = {year: {} for year in self.data_years}

            for year in data.keys():
                agg = [a for a in aggregates if a['data_year'] == year]
                for a in agg:
                    data[year][a['fund__name']] = {
                        'median': self._format_large_number(a['median']),
                        'count': self._format_large_number(a['count']),
                    }

            cache.set('benefit_aggregates', data, CACHE_TIMEOUT)

        return data

    @property
    def binned_benefit_data(self):
        data = self._cache.get('binned_benefit_data', {})

        if not data:
            DISTRIBUTION_BIN_NUM = 10
            DISTRIBUTION_MAX = 250000

            bin_size = DISTRIBUTION_MAX / DISTRIBUTION_BIN_NUM

            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT
                      data_year,
                      fund.name AS fund_name,
                      width_bucket(amount, 0, 250000, 10) AS bucket_index,
                      MAX(amount) AS max_value,
                      COUNT(*)
                    FROM pensions_benefit AS benefit
                    JOIN pensions_pensionfund AS fund
                    ON benefit.fund_id = fund.id
                    GROUP BY data_year, fund.name, bucket_index
                    ORDER BY data_year, fund.name, bucket_index
                ''')

                binned_data = {}

                for row in cursor:
                    data_year, fund, bucket_index, max_value, value = row
                    binned_data[(data_year, fund, bucket_index)] = (value, max_value)

            data = {year: {} for year in self.data_years}

            for year in data.keys():
                year_data = {}

                for fund in self.pension_funds:
                    fund_data = []

                    for i in range(DISTRIBUTION_BIN_NUM + 1):
                        value, max_value = binned_data.get((year, fund.name, i + 1), (0, 0))

                        lower = int(i * bin_size)
                        upper = int(lower + bin_size)

                        if i == DISTRIBUTION_BIN_NUM and max_value > upper:
                            upper = max_value

                        fund_data.append({
                            'y': int(value),  # number of benefits in given bin
                            'lower_edge': self._format_large_number(lower),
                            'upper_edge': self._format_large_number(upper),
                        })

                    year_data[fund.name] = fund_data

                data[year] = year_data

            cache.set('binned_benefit_data', data, CACHE_TIMEOUT)

        return data

    @property
    def funding_aggregates(self):
        '''
        {2017: [list, of, level, data]}
        '''
        data = {year: [] for year in self.data_years}

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT
                  data_year,
                  fund_type,
                  SUM(assets) AS funded_liability,
                  SUM(total_liability - assets) AS unfunded_liability
                FROM pensions_pensionfund AS fund
                JOIN pensions_annualreport AS report
                ON fund.id = report.fund_id
                GROUP BY data_year, fund_type
            ''')

            annual_reports = cursor.fetchall()

        for data_year, fund_type, funded_liability, unfunded_liability in annual_reports:
            container_name = '{}-container'.format(fund_type.lower())
            funded_liability = float(funded_liability)
            unfunded_liability = float(unfunded_liability)

            data[data_year].append(self._make_pie_chart(container_name, funded_liability, unfunded_liability))

        return data

    @property
    def fund_metadata(self):
        data = {year: {} for year in self.data_years}

        binned_benefit_data = self.binned_benefit_data
        median_benefits = self.benefit_aggregates

        for fund in self.pension_funds.prefetch_related('annual_reports'):
            for annual_report in fund.annual_reports.all():
                funded_liability = float(annual_report.assets)
                unfunded_liability = float(annual_report.unfunded_liability)
                normal_cost = float(annual_report.employer_normal_cost)
                amortization_cost = float(annual_report.amortization_cost)

                data[annual_report.data_year][fund.name] = {
                    'aggregate_funding': self._make_pie_chart('fund-container', funded_liability, unfunded_liability),
                    'amortization_cost': self._make_bar_chart('amortization-cost', normal_cost, amortization_cost),
                    'total_liability': self._format_large_number(int(annual_report.total_liability)),
                    'employer_contribution': self._format_large_number(int(annual_report.employer_contribution)),
                    'funding_level': int(annual_report.funded_ratio * 100),
                }

            for year in data.keys():
                fund_data = data[year].get(fund.name, {})

                fund_data.update({
                    'binned_benefit_data': binned_benefit_data[year][fund.name],
                    'median_benefit': median_benefits[year].get(fund.name, {}).get('median', 0),
                    'total_benefits': median_benefits[year].get(fund.name, {}).get('count', 0),
                })

                data[year][fund.name] = fund_data

        return data

    def _make_pie_chart(self, container, funded_liability, unfunded_liability):
        return {
            'container': container,
            'label_format': r'${point.label}',
            'total_liability': self._format_large_number(int(funded_liability + unfunded_liability)),
            'series_data': {
                'Name': 'Data',
                'data': [{
                    'name': 'Funded',
                    'y': funded_liability,
                    'label': self._format_large_number(int(funded_liability)),
                }, {
                    'name': 'Unfunded',
                    'y': unfunded_liability,
                    'label': self._format_large_number(int(unfunded_liability)),
                }],
            },
        }

    def _make_bar_chart(self, container, normal_cost, amortization_cost):
        return {
            'container': container,
            'pretty_amortization_cost': self._format_large_number(int(amortization_cost)),
            'pretty_employer_normal_cost': self._format_large_number(int(normal_cost)),
            'x_axis_categories': [''],
            'axis_label': 'Dollars',
            'funded': {
                'name': '<strong>Amortization Cost:</strong> Present cost of paying down past debt',
                'data': [amortization_cost],
                'color': '#dc3545',
                'legendIndex': 1,
            },
            'unfunded': {
                'name': '<strong>Employer Normal Cost:</strong> Projected cost to cover future benefits for current employees',
                'data': [normal_cost],
                'color': '#01406c',
                'legendIndex': 0,
            },
            'stacked': 'true',
        }


class BenefitListJson(BaseDatatableView):
    model = Benefit

    # define the columns that will be returned
    columns = [
        'first_name',
        'last_name',
        'amount',
        'years_of_service',
        'final_salary',
        'start_date',
        'status'
    ]

    # max number of records returned at a time; protects site from large
    # requests
    max_display_length = 500

    def filter_queryset(self, qs):
        qs = qs.filter(fund__name=self.request.GET['fund'],
                       data_year=int(self.request.GET['data_year']))

        search = self.request.GET.get('search[value]', None)

        if search:
            first_name = Q(first_name__istartswith=search)
            last_name = Q(last_name__istartswith=search)
            full_name = Q(full_name__istartswith=search)
            qs = qs.filter((first_name | last_name) | full_name)

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            json_data.append([
                item.first_name,
                item.last_name,
                self._format_currency(item.amount),
                item.years_of_service,
                self._format_currency(item.final_salary),
                item.start_date,
                item.status,
            ])

        return json_data

    def _format_currency(self, amount):
        if amount in ('', None, 'None'):
            return amount
        return '${}'.format(intcomma(amount))


def logout(request):
    log_out(request)
    return_to = urlencode({'returnTo': request.build_absolute_uri('/')})
    logout_url = 'https://%s/v2/logout?client_id=%s&%s' % \
                 (settings.SOCIAL_AUTH_AUTH0_DOMAIN, settings.SOCIAL_AUTH_AUTH0_KEY, return_to)
    return HttpResponseRedirect(logout_url)


def pong(request):
    try:
        from bga_database.deployment import DEPLOYMENT_ID
    except ImportError as e:
        return HttpResponse('Bad deployment: {}'.format(e), status=401)

    return HttpResponse(DEPLOYMENT_ID)


def flush_cache(request):
    if request.GET.get('key', '') == settings.CACHE_KEY:
        cache.clear()

    return HttpResponseRedirect(request.build_absolute_uri('/'))
