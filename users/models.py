# Not a real model, but django documentation suggests putting signal handlers
# here.
from registration.signals import user_activated
from django.contrib.auth.models import User
from django.contrib.auth import login

def activation_callback(sender, **kwargs):
    request = kwargs['request']
    user = kwargs['user']

    # We have to duplicate some functionality of contrib.auth here
    # This assumes that ModelBackend is used
    user = User.objects.get(username=user)
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request,user)

user_activated.connect(activation_callback)
