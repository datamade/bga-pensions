from django.db import models


class VintagedModel(models.Model):
    data_year = models.IntegerField()

    class Meta:
        abstract = True


class PensionFund(models.Model, VintagedModel):

    name = models.CharField(max_length=500)
    eligible_for_social_security = models.BooleanField()

    def median_annual_benefit(self, year):
        # self.benefits.filter(data_year=year)...
        pass


class AnnualReport(models.Model):

    fund = models.ForeignKey('Fund', related_name='annual_reports')
    total_liability = models.DecimalField(max_digits=20, decimal_places=2)
    assets = models.DecimalField(max_digits=20, decimal_places=2)
    employer_contribution = models.DecimalField(max_digits=20, decimal_places=2)
    employer_normal_cost = models.DecimalField(max_digits=20, decimal_places=2)

    @property
    def funded_ratio(self):
        return assets / total_liability

    @property
    def unfunded_liability(self):
        return total_liability - assets


class Benefit(models.Model, VintagedModel):

    fund = models.ForeignKey('Fund', related_name='benefits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(null=True, blank=True)


class Beneficiary(models.Model):

    benefit = models.OneToOneField('Benefit')
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    years_of_service = models.IntegerField()
    final_salary = models.DecimalField(max_digits=10, decimal_places=2)
