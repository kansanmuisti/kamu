from django import forms
from django.forms import ModelForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from kamu.joining.models import NewMember, Reference
from kamu.cms.models import Item
from django.db.models import Max

class NewMemberForm(ModelForm):
    class Meta:
        model = NewMember
        exclude = ('reference',)

# This ought to be in cashflow, but at least it is nicely self contained here
def generate_reference():
    q = Reference.objects.filter(refnum__startswith='2')
    q = q.aggregate(Max('refnum'))['refnum__max']
    if q:
        refid = str(int(q + 1))
    else:
        refid = "20000"
    Reference(refnum=refid).save()
    # Generates the checksum digit
    return refid + str(-sum(int(x)*[7,3,1][i%3] for i, x in enumerate(refid[::-1])) % 10)

def register(request):
    arg_dict = {}
    if request.method == 'POST':
        form = NewMemberForm(request.POST)
        if form.is_valid():
            newmember = form.save(commit=False)
            newmember.reference = generate_reference()
            newmember.save()
            request.session['joining_newmember'] = newmember
            return HttpResponseRedirect(reverse('joining.views.thankyou'))
    else:
        form = NewMemberForm()
    arg_dict['form'] = form
    arg_dict['content'] = Item.objects.retrieve_content('joining_new')
    return render_to_response('joining/new_member.html', arg_dict, RequestContext(request))

def thankyou(request):
    if not 'joining_newmember' in request.session:
        return HttpResponseRedirect('/')
    newmember = request.session['joining_newmember']
    del request.session['joining_newmember']
    arg_dict = {}
    arg_dict['content'] = Item.objects.retrieve_content('joining_thankyou')
    arg_dict['reference'] =  newmember.get_reference()
    arg_dict['sum'] = newmember.pledged_sum
    arg_dict['email'] = newmember.email

    return render_to_response('joining/confirm_application.html', arg_dict, RequestContext(request))
