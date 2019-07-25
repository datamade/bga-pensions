from urllib.parse import urlencode

from django.contrib.auth import logout as log_out
from django.conf import settings
from django.db.models import Max, Sum, Value
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from pensions.models import PensionFund, AnnualReport


class Index(TemplateView):
    template_name = 'index.html'

    @property
    def data_years(self):
        if not getattr(self, '_data_years', None):
            self._data_years = AnnualReport.objects.distinct('data_year')\
                                                   .values_list('data_year', flat=True)
        return self._data_years

    def _aggregate_funding(self, data_year):
        funded_liability = Sum('annual_reports__assets')
        unfunded_liability = Sum('annual_reports__total_liability') - Sum('annual_reports__assets')
        funding_levels = PensionFund.objects.values('fund_type')\
                                            .filter(annual_reports__data_year=data_year)\
                                            .annotate(funded=funded_liability,
                                                      unfunded=unfunded_liability)

        chart_data = []

        for level in funding_levels:
            container_name = '{}-container'.format(level['fund_type'].lower())

            level_data = [{
                'name': level['fund_type'].title(),
                'container': container_name,
                'data': [{
                    'name': 'Funded Liability',
                    'y': float(level['funded']),
                    'legendIndex': 1,
                }, {
                    'name': 'Unfunded Liability',
                    'y': float(level['unfunded']),
                    'legendIndex': 0,
                }],
            }]

            chart_data.append(level_data)

        return chart_data

    def _fund_metadata(self, data_year):
        data_by_fund = {}

        for fund in PensionFund.objects.all():
            try:
                annual_report = fund.annual_reports.get(data_year=data_year)
            except AnnualReport.DoesNotExist:
                annual_report = None

            fund_data = {}

            if annual_report:
                fund_data = {
                    'aggregate_funding': [{
                        'name': fund.name,
                        'container': 'fund-container',
                        'data': [{
                            'name': 'Funded Liability',
                            'y': float(annual_report.assets),
                            'legendIndex': 1,
                        }, {
                            'name': 'Unfunded Liability',
                            'y': float(annual_report.unfunded_liability),
                            'legendIndex': 0,
                        }],
                    }],
                    'funding_level': annual_report.funded_ratio * 100,
                    'employer_normal_cost': float(annual_report.employer_normal_cost),
                    'amortization_cost': annual_report.amortization_cost,
                }

            data_by_fund[fund.name] = fund_data

        return data_by_fund

    def _data_by_year(self):
        data_by_year = {}

        for year in self.data_years:
            year_data = {
                'aggregate_funding': self._aggregate_funding(year),
                'data_by_fund': self._fund_metadata(year),
            }

            data_by_year[year] = year_data

        return data_by_year

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['data_years'] = list(self.data_years)
        context['pension_funds'] = list(PensionFund.objects.all())
        context['data_by_year'] = self._data_by_year()

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
