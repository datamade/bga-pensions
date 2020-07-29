from django.db import models


class VintagedModel(models.Model):
    '''
    Convenience base class that adds a data year attribute to models that
    should be filterable by year.
    '''
    data_year = models.IntegerField()

    class Meta:
        abstract = True


class PensionFund(models.Model):
    '''
    One of the pension systems tracked in the database.
    '''
    FUND_TYPE_CHOICES = [
        ('STATE', 'State'),
        ('COUNTY', 'County'),
        ('CHICAGO', 'Chicago Municipal'),
        ('DOWNSTATE', 'Downstate'),
    ]

    name = models.CharField(max_length=500)
    fund_type = models.CharField(max_length=256, choices=FUND_TYPE_CHOICES)

    def __str__(self):
        return self.name

    def median_annual_benefit(self, year):
        # self.benefits.filter(data_year=year)...
        pass


class AnnualReport(VintagedModel):
    '''
    Annual plan and financial metadata for each pension fund. Metadata may
    be reported by calendar year or by fiscal year starting July 1. They are
    compiled by hand from Commission on Government Forecasting and
    Accountability reports, as well as reports from each fund.
    '''

    REPORTING_PERIOD_CHOICES = [
        ('CALENDAR', 'Calendar year'),
        ('FISCAL', 'Fiscal year'),
    ]

    fund = models.ForeignKey('PensionFund', related_name='annual_reports', on_delete=models.CASCADE)
    eligible_for_social_security = models.BooleanField()
    total_liability = models.DecimalField(max_digits=20, decimal_places=2)
    assets = models.DecimalField(max_digits=20, decimal_places=2)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2)
    employer_normal_cost = models.DecimalField(max_digits=20, decimal_places=2)
    reporting_period = models.CharField(max_length=256, choices=REPORTING_PERIOD_CHOICES)

    def __str__(self):
        return '{} – {}'.format(self.fund, self.data_year)

    @property
    def funded_ratio(self):
        return float(self.assets / self.total_liability)

    @property
    def unfunded_liability(self):
        return float(self.total_liability - self.assets)

    @property
    def amortization_cost(self):
        if self.employer_contribution > self.employer_normal_cost:
            return float(self.employer_contribution - self.employer_normal_cost)
        else:
            return 0


class Benefit(VintagedModel):
    '''
    Individual pension benefit. Benefit data are reported by each pension fund.

    Beneficiaries are not linked year over year, i.e., Beneficiary objects
    across years may refer to the same person.

    Starting in 2018, data contain benefit status, e.g., "retiree", "widow/er",
    or "disability".
    '''

    fund = models.ForeignKey('PensionFund', related_name='benefits', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    full_name = models.CharField(max_length=256*2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    years_of_service = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return ' '.join([self.first_name, self.last_name])
