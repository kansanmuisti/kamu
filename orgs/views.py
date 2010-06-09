from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from kamu.orgs.models import Organization, SessionScore
from kamu.orgs.forms import AddOrgForm, ModifyOrgForm, ModifyScoreForm

from kamu.votes.models import PlenarySession, Session

import os

def list_orgs(request):
    orgs = Organization.objects.order_by('name')
    arg_dict = { 'org_list': orgs, 'active_page': 'orgs' }

    ctx = RequestContext(request)
    return render_to_response('list_orgs.html', arg_dict, ctx)

def add_organization(org, admin, tmpf):
    modify_organization(org, admin, tmpf)

    group = org.get_group()
    admin.groups.add(group)

def modify_organization(org, admin, tmpf):
    if tmpf:
        #New logo passed in
        logof = os.path.join('images/orgs', org.url_name + '.png')
        full_path = os.path.join(settings.MEDIA_ROOT, logof)
        os.rename(os.path.join(settings.MEDIA_ROOT, tmpf), full_path)
        org.logo = logof

    org.save()
    # Admin might be changed here too?

# Simple helper to build an Organization based on form data both in
# AddOrgForm and ModifyOrgForm
def build_org(form, org = Organization()):
    cd = form.cleaned_data
    org.name = cd['name']
    org.info_link = cd['info_link']
    org.description = cd['description']
    org.logo = form.logo_path

    return org

@login_required
def add_org(request):
    arg_dict = {}

    # Preview clicked (or another submit button if such is later added)
    if request.method == 'POST':
        form = AddOrgForm(request.POST, request.FILES)

        if form.is_valid():
            org = build_org(form)
            org.url_name = org.generate_url_name()

            if 'preview' in request.POST:
                request.session['org_new'] = org
                path = reverse('orgs.views.preview_add_org')
                return HttpResponseRedirect(path)
    # Either returning through preview of beginning of addition
    else:
        # This means that someone interrupting modifying an organization
        # will get the its info for initial data while adding
        if 'org_new' in request.session:
            org = request.session['org_new']
            arg_dict['org'] = org
            initial = {}
            initial['name'] = org.name
            initial['description'] = org.description
            initial['info_link'] = org.info_link
            form = AddOrgForm(initial=initial)
        else:
            form = AddOrgForm()
    arg_dict['form'] = form
    return render_to_response('add_org.html', arg_dict, RequestContext(request))

@login_required
def preview_add_org(request):
    # Only allow preview if add_org has added the contents to preview
    if 'org_new' in request.session:
        org = request.session['org_new']
    else:
        raise Http404
    # Preview confirmed with submit button in form
    if request.method == 'POST':
        add_organization(org, request.user, str(org.logo))
        del request.session['org_new']
        kwargs = { 'org': org.url_name }
        path = reverse('orgs.views.show_org', kwargs=kwargs)
        return HttpResponseRedirect(path)
    return render_to_response('preview_org.html', {'org': org})

@login_required
def modify_org(request, org):
    try:
        org = Organization.objects.get(url_name = org)
    except Organization.DoesNotExist:
        raise Http404
    if not org.is_admin(request.user):
        return HttpResponseForbidden()
    if request.method == "POST":
        form = ModifyOrgForm(org, request.POST, request.FILES)
        if form.is_valid():
            build_org(form, org)
            # We allow changing the link string for org for now
            org.new_url_name = org.generate_url_name()

            # Is there any other case for POST than preview?
            # ie. is this 'if' redundant?
            if 'preview' in request.POST:
                request.session['org_new'] = org
                kwargs = { 'org': org.url_name }
                path = reverse('orgs.views.preview_modify_org', kwargs=kwargs)
                return HttpResponseRedirect(path)
    # This is either new request for modification
    # or a user returning from preview
    else:
        if 'org_new' in request.session:
            # User is returning from some preview
            org_new = request.session['org_new']
            # Only use the org_new if we are still
            # editing the same org
            if org_new.url_name == org.url_name:
                org = org_new
            else:
                del request.session['org_new']

        initial = {}
        initial['name'] = org.name
        initial['description'] = org.description
        initial['info_link'] = org.info_link
        form = ModifyOrgForm(org, initial=initial)

    args_dict = { 'form': form, 'org': org, 'modify': True }
    return render_to_response('add_org.html', args_dict, RequestContext(request))

@login_required
# org (containing the slug string) is here just to get consistent urls
def preview_modify_org(request, org):
    org_slug = org
    # Only allow preview if add_org has added the contents to preview
    if 'org_new' in request.session:
        org = request.session['org_new']
    else:
        raise Http404
    # Let's check the URL is correct, although it really does not matter?
    if org.url_name != org_slug:
        return HttpResponseForbidden()

    if request.method == 'POST':
        # User confirmed preview
        org.url_name = org.new_url_name
        modify_organization(org, request.user, str(org.logo))
        del request.session['org_new']
        kwargs = { 'org': org.url_name }
        path = reverse('orgs.views.show_org', kwargs=kwargs)
        return HttpResponseRedirect(path)
    return render_to_response('preview_org.html', {'org': org, 'modify': True})

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
