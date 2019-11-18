"""bga_database URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.cache import cache_page

from pensions import views as pension_views


urlpatterns = [
    path('', cache_page(60*60*24*7)(pension_views.Index.as_view())),
    path('user-guide/', pension_views.UserGuide.as_view()),
    path('benefits/', pension_views.BenefitListJson.as_view(), name='benefit_list_json'),
    path('admin/', admin.site.urls),
    path('pong/', pension_views.pong),
    path('flush/', pension_views.flush_cache),
    path('salsa/', include('salsa_auth.urls')),
    path('', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
