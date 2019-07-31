import django_filters

from pensions.models import Benefit, PensionFund


class BenefitFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='iexact')
    fund = django_filters.ModelChoiceFilter(queryset=PensionFund.objects.all())

    class Meta:
        model = Benefit
        fields = ['data_year']

    @property
    def qs(self):
        fund = PensionFund.objects.get(name='Downstate/Suburban Teachers (TRS)')
        year = 2018

        if self.request:
            fund_id = self.request.get('fund')

            if fund_id:
                fund = PensionFund.objects.get(id=fund_id)

            year = self.request.get('year', year)

        return super().qs.filter(fund=fund, data_year=year)


'''
TO-DO: Wire up AJAX endpoint that returns the filter queryset. Handle options
for pagination and sorted. See: https://datatables.net/manual/server-side
'''
