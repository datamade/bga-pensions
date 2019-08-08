from urllib.parse import urlencode

from django.contrib.humanize.templatetags.humanize import intword
from django.contrib.auth import logout as log_out
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from django_datatables_view.base_datatable_view import BaseDatatableView

from pensions.models import PensionFund, Benefit


class Index(TemplateView):
    template_name = 'index.html'

    @property
    def data_years(self):
        return list(range(2012, 2020))
#        if not hasattr(self, '_data_years'):
#            self._data_years = Benefit.objects.distinct('data_year')\
#                                              .values_list('data_year', flat=True)
#        return self._data_years

    @property
    def pension_funds(self):
        if not hasattr(self, '_pension_funds'):
            self._pension_funds = PensionFund.objects.all()
        return self._pension_funds

    def _binned_benefit_data(self):
        DISTRIBUTION_BIN_NUM = 10
        DISTRIBUTION_MAX = 250000

        bin_size = DISTRIBUTION_MAX / DISTRIBUTION_BIN_NUM

        benefit_json = cache.get('binned_benefit_data', {})

        if not benefit_json:
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

            benefit_json = {year: {} for year in self.data_years}

            for year in benefit_json.keys():
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
                            'y': int(value),  # number of salaries in given bin
                            'lower_edge': intword(lower),
                            'upper_edge': intword(upper),
                        })

                    year_data[fund.name] = fund_data

                benefit_json[year] = year_data

            cache.set('binned_benefit_data', benefit_json, 600)

        return benefit_json

    def _aggregate_funding(self):
        '''
        {2017: [list, of, level, data]}
        '''
        data_by_level = {year: [] for year in self.data_years}

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

            data_by_level[data_year].append({
                'container': container_name,
                'label_format': r'${point.label}',
                'total_liability': intword(int(funded_liability + unfunded_liability)),
                'series_data': {
                    'Name': 'Data',
                    'data': [{
                        'name': 'Funded',
                        'y': float(funded_liability),
                        'label': intword(int(funded_liability)),
                    }, {
                        'name': 'Unfunded',
                        'y': float(unfunded_liability),
                        'label': intword(int(unfunded_liability)),
                    }],
                },
            })

        return data_by_level

    def _fund_metadata(self):
        '''
        {2017: {'fund': {}, 'fund': {}}}
        '''
        data_by_fund = {year: {} for year in self.data_years}

        binned_benefit_data = self._binned_benefit_data()

        for fund in self.pension_funds.prefetch_related('annual_reports'):
            for annual_report in fund.annual_reports.all():
                data_by_fund[annual_report.data_year][fund.name] = {
                    'aggregate_funding': {
                        'container': 'fund-container',
                        'label_format': r'${point.label}',
                        'series_data': {
                            'name': 'Data',
                            'data': [{
                                'name': 'Funded',
                                'y': float(annual_report.assets),
                                'label': intword(int(annual_report.assets))
                            }, {
                                'name': 'Unfunded',
                                'y': annual_report.unfunded_liability,
                                'label': intword(int(annual_report.unfunded_liability))
                            }],
                        },
                    },
                    'amortization_cost': {
                        'container': 'amortization-cost',
                        'name_align': 'left',
                        'pretty_amortization_cost': intword(int(annual_report.amortization_cost)),
                        'pretty_employer_normal_cost': intword(int(annual_report.employer_normal_cost)),
                        'x_axis_categories': [''],
                        'axis_label': 'Dollars',
                        'funded': {
                            'name': '<strong>Amortization Cost:</strong> Present cost of paying down past debt',
                            'data': [annual_report.amortization_cost],
                            'color': '#dc3545',
                            'legendIndex': 1,
                        },
                        'unfunded': {
                            'name': '<strong>Employer Normal Cost:</strong> Projected cost to cover future benefits for current employees',
                            'data': [float(annual_report.employer_normal_cost)],
                            'color': '#01406c',
                            'legendIndex': 0,
                        },
                        'stacked': 'true',
                    },
                    'total_liability': intword(int(annual_report.assets) + int(annual_report.unfunded_liability)),
                    'employer_contribution': intword(annual_report.amortization_cost + float(annual_report.employer_normal_cost)),
                    'funding_level': int(annual_report.funded_ratio * 100),
                }

            for year in self.data_years:
                fund_data = data_by_fund[year].get(fund.name, {})
                fund_data['binned_benefit_data'] = binned_benefit_data[year][fund.name]
                data_by_fund[year][fund.name] = fund_data

        return data_by_fund

    def _data_by_year(self):
        data_by_year = {}

        data_by_fund = self._fund_metadata()
        aggregate_funding = self._aggregate_funding()

        for year in self.data_years:
            year_data = {
                'aggregate_funding': aggregate_funding[year],
                'data_by_fund': data_by_fund[year],
            }

            data_by_year[year] = year_data

        return data_by_year

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['data_years'] = list(self.data_years)
        context['pension_funds'] = self.pension_funds
        context['data_by_year'] = self._data_by_year()

        return context


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
            qs = qs.filter(first_name | last_name)

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            json_data.append([
                item.first_name,
                item.last_name,
                item.amount,
                item.years_of_service,
                item.final_salary,
                item.start_date,
                item.status,
            ])

        return json_data


def logout(request):
    log_out(request)
    return_to = urlencode({'returnTo': request.build_absolute_uri('/')})
    logout_url = 'https://%s/v2/logout?client_id=%s&%s' % \
                 (settings.SOCIAL_AUTH_AUTH0_DOMAIN, settings.SOCIAL_AUTH_AUTH0_KEY, return_to)
    return HttpResponseRedirect(logout_url)


def pong(request):
    from django.http import HttpResponse

    try:
        from bga_database.deployment import DEPLOYMENT_ID
    except ImportError as e:
        return HttpResponse('Bad deployment: {}'.format(e), status=401)

    return HttpResponse(DEPLOYMENT_ID)
