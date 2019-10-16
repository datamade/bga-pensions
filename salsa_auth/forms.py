from django import forms


class BootstrapMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class SignUpForm(BootstrapMixin, forms.Form):
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')
    zip_code = forms.CharField(label='Zip code')


class LoginForm(BootstrapMixin, forms.Form):
    email = forms.EmailField(label='Email')

    def check_salsa(self):
        pass
