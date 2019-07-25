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
        percent_funded = Sum('annual_reports__assets') / Sum('annual_reports__total_liability')
        funding_levels = PensionFund.objects.values('fund_type')\
                                            .filter(annual_reports__data_year=data_year)\
                                            .annotate(percent_funded=percent_funded,
                                                      percent_unfunded=Value(1.0) - percent_funded)

        chart_data = []

        for level in funding_levels:
            container_name = '{}-container'.format(level['fund_type'].lower())

            level_data = [{
                'name': level['fund_type'].title(),
                'container': container_name,
                'data': [{
                    'name': 'Percent Funded',
                    'y': float(level['percent_funded']),
                    'legendIndex': 1,
                }, {
                    'name': 'Percent Unfunded',
                    'y': float(level['percent_unfunded']),
                    'legendIndex': 0,
                }],
            }]

            chart_data.append(level_data)

        return chart_data

    def _data_by_year(self):
        data_by_year = {}

        for year in self.data_years:
            year_data = {
                'aggregate_funding': self._aggregate_funding(year)
            }

            data_by_year[year] = year_data

        return data_by_year

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['data_years'] = list(self.data_years)
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
