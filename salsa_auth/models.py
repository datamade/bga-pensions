from django.contrib.auth.models import User
from django.db import models


class UserZipCode(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=25)
