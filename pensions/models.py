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

    name = models.CharField(max_length=500)

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

    @property
    def funded_ratio(self):
        return assets / total_liability

    @property
    def unfunded_liability(self):
        return total_liability - assets


class Benefit(VintagedModel):
    '''
    Individual pension benefit. Both Benefit and Beneficiary are sourced from
    data on individual benefits reported by each pension fund. Starting in
    2018, data contain benefit status, e.g., "retiree", "widow/er", or
    "disability".
    '''

    fund = models.ForeignKey('PensionFund', related_name='benefits', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=256, null=True, blank=True)


class Beneficiary(models.Model):
    '''
    Person receiving individual pension benefit. Beneficiaries are not linked
    year over year, i.e., Beneficiary objects across years may refer to the
    same person.
    '''

    benefit = models.OneToOneField('Benefit', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    years_of_service = models.IntegerField()
    final_salary = models.DecimalField(max_digits=10, decimal_places=2)
