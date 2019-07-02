from django.contrib import admin

from pensions.models import PensionFund, AnnualReport


class PensionFundAdmin(admin.ModelAdmin):
    pass


class AnnualReportAdmin(admin.ModelAdmin):
    pass


admin.site.register(PensionFund, PensionFundAdmin)
admin.site.register(AnnualReport, AnnualReportAdmin)
