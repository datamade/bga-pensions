from django.urls import include, path, re_path

from salsa_auth import views as salsa_views


app_name = 'salsa_auth'
urlpatterns = [
    path('salsa/login/', salsa_views.LoginForm.as_view(), name='login'),
    path('salsa/signup/', salsa_views.SignUpForm.as_view(), name='signup'),
    path(
        '^verify/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        salsa_views.VerifyEmail.as_view(),
        name='verify'
    ),
    path('salsa/authenticate', salsa_views.Authenticate.as_view(), name='auth'),
    path('salsa/logout/', salsa_views.Logout.as_view(), name='logout'),
]
