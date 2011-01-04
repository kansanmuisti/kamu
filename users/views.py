from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.views import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.template import RequestContext
from django.core.urlresolvers import reverse
from facebook.api import get_user_from_cookie, delete_cookie

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/")
    else:
        form = UserCreationForm()
    return render_to_response("register.html", {
        'form': form,
    })

def login(request):
    user = get_user_from_cookie(request.COOKIES)
    if user and not request.user.is_authenticated():
        url = reverse('facebook_connect')
        next = request.REQUEST.get('next')
	if next:
            url += '?next=%s' % next
	return HttpResponseRedirect(url)
    return auth_login(request)

def logout(request):
    auth_logout(request)
    resp = render_to_response("registration/logout.html",
                              context_instance=RequestContext(request))
    return resp
