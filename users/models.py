# Not a real model, but django documentation suggests putting signal handlers
# here.
from registration.signals import user_activated
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import models

class KamuProfile(models.Model):
    GENDERS = [
        ('F', u'Female'),
        ('M', u'Male'),
    ]
    user = models.ForeignKey(User, unique=True)

    facebook_id = models.CharField(max_length=32, blank=True, null=True, unique=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDERS)
    location = models.CharField(max_length=80, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to='images/users')

def activation_callback(sender, **kwargs):
    request = kwargs['request']
    user = kwargs['user']

    # We have to duplicate some functionality of contrib.auth here
    # This assumes that ModelBackend is used
    user = User.objects.get(username=user)
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request,user)

user_activated.connect(activation_callback)
