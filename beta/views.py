from django import forms
from django.forms import ModelForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from kamu.beta.models import Tester

class TesterForm(ModelForm):
    class Meta:
        model = Tester

def register(request):
    arg_dict = {}
    if request.method == 'POST':
        form = TesterForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('kamu.beta.views.thankyou'))
    else:
        form = TesterForm()
    arg_dict['form'] = form
    return render_to_response('add_beta.html', arg_dict, RequestContext(request))

def thankyou(request):
    return render_to_response('confirm_beta.html', {}, RequestContext(request))
