from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from kamu.orgs.models import Organization, SessionScore
from kamu.orgs.forms import AddOrgForm, ModifyScoreForm

from kamu.votes.models import PlenarySession, Session

import os

def list_orgs(request):
    orgs = Organization.objects.order_by('name')
    arg_dict = { 'org_list': orgs, 'active_page': 'orgs' }

    ctx = RequestContext(request)
    return render_to_response('list_orgs.html', arg_dict, ctx)

def add_organization(org, admin, tmpf):
    logof = os.path.join('images/orgs', org.url_name + '.png')
    full_path = os.path.join(settings.MEDIA_ROOT, logof)
    os.rename(os.path.join(settings.MEDIA_ROOT, tmpf), full_path)
    org.logo = logof
    org.save()

    group = org.get_group()
    admin.groups.add(group)

@login_required
def add_org(request):
    arg_dict = {}
    if request.method == 'POST':
        form = AddOrgForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            org = Organization()
            org.name = cd['name']
            org.info_link = cd['info_link']
            org.description = cd['description']
            org.logo = form.logo_path
            org.url_name = org.generate_url_name()
            arg_dict['org'] = org
            if 'submit' in request.POST:
                add_organization(org, request.user, form.logo_path)
                path = reverse('orgs.views.show_org', kwargs={ 'org': org.url_name })
                return HttpResponseRedirect(path)
    else:
        form = AddOrgForm()
    arg_dict['form'] = form
    return render_to_response('add_org.html', arg_dict, RequestContext(request))

@login_required
def modify_org(request, org):
    try:
        org = Organization.objects.get(url_name = org)
    except Organization.DoesNotExist:
        raise Http404
    if not org.is_admin(request.user):
        return HttpResponseForbidden()
    initial = {}
    initial['name'] = org.name
    initial['description'] = org.description
    initial['info_link'] = org.info_link
    form = AddOrgForm(initial=initial)
    return render_to_response('add_org.html', {'form': form}, RequestContext(request))

def show_org(request, org):
    try:
        org = Organization.objects.get(url_name = org)
    except Organization.DoesNotExist:
        raise Http404
    org.description = org.description.replace('\n', '\n\n')
    scores = SessionScore.objects.filter(org = org).order_by('session__plenary_session__date')
    args = { 'org': org, 'scores': scores }
    if org.is_admin(request.user):
        args['is_admin'] = True
    return render_to_response('show_org.html', args, context_instance = RequestContext(request))

@login_required
def modify_score(request, org, sess, plsess):
    try:
        org = Organization.objects.get(url_name = org)
        plsess = PlenarySession.objects.get(url_name = plsess)
        sess = Session.objects.get(plenary_session = plsess, number = sess)
        sess.info = sess.info.replace('\n', '\n\n')
    except (Organization.DoesNotExist, PlenarySession.DoesNotExist, Session.DoesNotExist):
        raise Http404
    if not org.is_admin(request.user):
        return HttpResponseForbidden()
    try:
        score = SessionScore.objects.get(org = org, session = sess)
    except SessionScore.DoesNotExist:
        score = None

    if request.method == 'POST':
        form = ModifyScoreForm(request.POST)
        if form.is_valid():
           score = SessionScore()
           score.session = sess
           score.org = org
           score.rationale = form.cleaned_data['rationale']
           score.score = form.cleaned_data['score']
           score.save()

           kwargs = { 'plsess': plsess.url_name, 'sess': sess.number }
           path = reverse('votes.views.show_session', kwargs=kwargs)
           return HttpResponseRedirect(path)

    if score:
        form = ModifyScoreForm(score)
    else:
        form = ModifyScoreForm(initial = { 'score': 0 })
    form.max_score = SessionScore.SCORE_MAX

    args = { 'org': org, 'session': sess, 'form': form }
    return render_to_response('modify_score.html', args, context_instance = RequestContext(request))
