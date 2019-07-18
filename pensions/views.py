from urllib.parse import urlencode

from django.contrib.auth import logout as log_out
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView


class Index(TemplateView):
    template_name = 'index.html'


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
