from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import FormView, TemplateView

from salsa_auth.forms import SignUpForm, LoginForm
from salsa_auth.models import UserZipCode
from salsa_auth.tokens import account_activation_token


class BaseTemplateMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['base_template_name'] = getattr(settings, 'SALSA_AUTH_BASE_TEMPLATE_NAME', 'base.html')
        return context


class SignUpForm(BaseTemplateMixin, FormView):
    form_class = SignUpForm
    template_name = 'signup.html'

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            user = self._make_user(form.cleaned_data)

            # TO-DO: Potentially intercept SMTP error for undeliverable mail here
            self._send_verification_email(user)

            message =  'Please check your email for a verification code.'

            if message not in [m.message for m in messages.get_messages(self.request)]:
                messages.add_message(self.request, messages.INFO, message)

            return redirect('/')

        return super().post(*args, **kwargs)

    def _make_user(self, form_data):
        zip_code = form_data.pop('zip_code')

        user = User.objects.create(**form_data, username=str(uuid4()).split('-')[0])
        user.set_unusable_password()
        user.save()

        user_zip = UserZipCode.objects.create(user=user, zip_code=zip_code)

        return user

    def _send_verification_email(self, user):
        current_site = get_current_site(self.request)
        email_subject = 'Activate Your Account'
        message = render_to_string('emails/activate_account.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        to_email = user.email
        send_mail(email_subject, message, '6ec675b8a9-10e75e@inbox.mailtrap.io', [to_email])


class LoginForm(BaseTemplateMixin, FormView):
    form_class = LoginForm
    template_name = 'login.html'

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def post(self):
        #if self.form.is_valid():
            # check user
            # if not user
                # redirect to signup
            # if user
                # authenticate
                # TO-DO: best way to do this???
        pass


class VerifyEmail(TemplateView):
    def get(self, request, uidb64, token):
        '''
        https://simpleisbetterthancomplex.com/tutorial/2016/08/24/how-to-create-one-time-link.html
        '''
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            # add to salsa
            return redirect('authenticate')
        else:
            # invalid link
            return redirect('signup')

    def add_to_salsa(self, user):

        params = {
            'zipcode': user.userzipcode.zipcode,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }

        payload = settings.SALSA_PAYLOAD % params

        signup = requests.post(settings.SALSA_URL,
                               data=payload,
                               headers={'content-type':
                                        'application/json; charset=utf-8'})

        # Capture exceptions (use the logging module)


class Authenticate(TemplateView):
    def get(self, *args, **kwargs):
        '''
        TO-DO: Can this be done serverside, or do we need to set the cookies
        clientside, i.e., with JavaScript?
        '''
        pass


class Logout(TemplateView):
    pass
