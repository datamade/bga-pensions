from django.shortcuts import render
from django.views.generic import TemplateView


class Index(TemplateView):
    template_name = 'base.html'


def pong(request):
    from django.http import HttpResponse

    try:
        from bga_database.deployment import DEPLOYMENT_ID
    except ImportError as e:
        return HttpResponse('Bad deployment: {}'.format(e), status=401)

    return HttpResponse(DEPLOYMENT_ID)
