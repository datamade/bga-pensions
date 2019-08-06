from urllib.parse import urlencode

from django.contrib.humanize.templatetags.humanize import intword
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
        '''
        TODO: Tie this to individual data
        '''
        return list(range(2012, 2019))

    def _aggregate_funding(self, data_year):
        funding_levels = PensionFund.objects.values('fund_type')\
                                            .filter(annual_reports__data_year=data_year)\
                                            .annotate(funded_liability=Sum('annual_reports__assets'),
                                                      unfunded_liability=Sum('annual_reports__total_liability') - Sum('annual_reports__assets'))

        chart_data = []

        for level in funding_levels:
            container_name = '{}-container'.format(level['fund_type'].lower())
            chart_title = '<b>{0} Pension System</b><br /><span class="small">{1}</span>'.format(level['fund_type'].title(), data_year)
            chart_data.append({
                'container': container_name,
                'name': chart_title,
                'label_format': r'${point.label}',
                'total_liability': intword(int(level['funded_liability']) + int(level['unfunded_liability'])),
                'series_data': {
                    'Name': 'Data',
                    'data': [{
                        'name': 'Funded liability',
                        'y': float(level['funded_liability']),
                        'label': intword(int(level['funded_liability'])),
                    }, {
                        'name': 'Unfunded liability',
                        'y': float(level['unfunded_liability']),
                        'label': intword(int(level['unfunded_liability'])),
                    }],
                },
            })

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
                    'aggregate_funding': {
                        'container': 'fund-container',
                        'name': '<b>Funding Distribution</b><br /><span class="small">{0}<span><br /><span class="small">{1}</span>'.format(fund.name.upper(), data_year),
                        'label_format': r'${point.label}',
                        'series_data': {
                            'name': 'Data',
                            'data': [{
                                'name': 'Funded liability',
                                'y': float(annual_report.assets),
                                'label': intword(int(annual_report.assets))
                            }, {
                                'name': 'Unfunded liability',
                                'y': annual_report.unfunded_liability,
                                'label': intword(int(annual_report.unfunded_liability))
                            }],
                        },
                    },
                    'amortization_cost': {
                        'container': 'amortization-cost',
                        'name': '<b>Employer Contribution Distribution</b><br /><span class="small">{0}<span><br /><span class="small">{1}</span>'.format(fund.name.upper(), data_year),
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
                    'employer_contribution': intword(annual_report.amortization_cost + float(annual_report.employer_normal_cost)),
                    'funding_level': int(annual_report.funded_ratio * 100),
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
