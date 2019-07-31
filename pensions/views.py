import itertools
from urllib.parse import urlencode

from django.contrib.humanize.templatetags.humanize import intword
from django.contrib.auth import logout as log_out
from django.conf import settings
from django.db import connection
from django.db.models import Max, Sum, Value
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from pensions.models import PensionFund, AnnualReport


class Index(TemplateView):
    template_name = 'index.html'

    @property
    def data_years(self):
        '''
        TODO: Tie this to individual data
        '''
        return list(range(2012, 2019))

    @property
    def pension_funds(self):
        if not hasattr(self, '_pension_funds'):
            self._pension_funds = PensionFund.objects.all()

        return self._pension_funds

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
        from pensions.filters import BenefitFilter
        from pensions.models import Benefit

        context = super().get_context_data(*args, **kwargs)

        context['data_years'] = list(self.data_years)
        context['pension_funds'] = self.pension_funds
        context['data_by_year'] = self._data_by_year()

        context['person_filter'] = BenefitFilter(request=self.request.GET,
                                                 queryset=Benefit.objects.all())

        return context


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
