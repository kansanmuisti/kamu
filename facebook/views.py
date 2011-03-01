from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query_utils import Q
from django.contrib.csrf.middleware import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from kamu.users.models import KamuProfile
from facebook.forms import RegistrationForm
from facebook.api import get_user_from_cookie, do_request, FacebookError
from facebook.api import delete_cookie
from httpstatus import Http403
from PIL import Image
import StringIO
import os
import re
import tempfile
import base64
import hashlib
import hmac
import simplejson as json

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "=" * padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def redirect_with_next(request, url):
    next = request.REQUEST.get('next')
    if next and not next.startswith(request.path):
        url += '?next=%s' % next
    return HttpResponseRedirect(url)

def get_profile_class():
    profile_model = settings.AUTH_PROFILE_MODULE.split('.')[-1]
    profile_class = ContentType.objects.get(model=profile_model.lower())
    return profile_class.model_class()

def get_profile_by_fb_id(id):
    profile_class = get_profile_class()
    try:
        profile = profile_class.objects.get(facebook_id=id)
    except ObjectDoesNotExist:
        return None
    return profile

def fetch_user_data(request, uid, access_token):
    try:
        resp = do_request(access_token, uid)
    except FacebookError as e:
        if e.type == "OAuthException":
            return None
        else:
            raise
    me = resp

    picture = do_request(access_token, uid + "/picture", raw=True)
    im = Image.open(StringIO.StringIO(picture))
    if im.size != (50, 50):
        raise Exception("Invalid image")
    tmpf = None
    if 'fb_portrait' in request.session:
        try:
            fn = os.path.join(settings.MEDIA_ROOT, request.session['fb_portrait'])
            tmpf = (os.open(fn, os.O_WRONLY), fn)
        except OSError:
            tmpf = None
    if not tmpf:
        dir = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP_DIR)
        tmpf = tempfile.mkstemp(suffix='.png', dir=dir)
        os.chmod(tmpf[1], 0644)
    path = os.path.join(settings.MEDIA_TMP_DIR, os.path.basename(tmpf[1]))

    file = os.fdopen(tmpf[0], "w")
    im.save(file, "png")
    file.close()

    args = {'info': me, 'portrait': path}

    return args

def create_fb_user(username, fb_data):
    info = fb_data['info']

    user = User.objects.create_user(username, info['email']) #FIXME
    user.first_name = info['first_name']
    user.last_name = info['last_name']

    profile_model = settings.AUTH_PROFILE_MODULE.split('.')[-1]
    profile_class = ContentType.objects.get(model=profile_model.lower()).model_class()
    profile = profile_class()
    profile.facebook_id = fb_data['uid']
    if 'location' in info:
        profile.location = info['location']['name']
    if 'birthday' in info:
        bd = info['birthday'].split('/')
        profile.birthday = '-'.join((bd[2], bd[0], bd[1]))

    image = os.path.join("images/users/", "%s.png" % username)
    fn = os.path.join(settings.MEDIA_ROOT, image)
    tmp_fn = os.path.join(settings.MEDIA_ROOT, fb_data['portrait'])
    os.rename(tmp_fn, fn)

    user.save()
    profile.user = user
    profile.save()

    return user

def register_form(request):
    fb_user = get_user_from_cookie(request.COOKIES)
    if not fb_user:
        raise Http403()

    if request.method == 'POST':
        if not 'fb_reg_data' in request.session:
            raise Http400()
        fb_data = request.session['fb_reg_data']
        form = RegistrationForm(request.POST)
        if form.is_valid():
            create_fb_user(form.cleaned_data['username'], fb_data)
            user = authenticate(facebook_id=fb_data['uid'])
            login(request, user)
            url = reverse('registration_activation_complete')
	    return HttpResponseRedirect(url)
    else:
        fb_data = fetch_user_data(request, fb_user['uid'],
                                  fb_user['access_token'])
        if not fb_data:
            url = reverse('login')
            resp = redirect_with_next(request, url)
            delete_cookie(resp)
            return resp

        fb_data['uid'] = fb_user['uid']
        fb_data['access_token'] = fb_user['access_token']
        request.session['fb_reg_data'] = fb_data

        user_data = fb_data['info']
        # Try to find a default account name
        account = user_data['link'].split('/')[-1]
        if account.startswith('profile.php'):
            # No account shortname defined, use first and last names.
            account = slugify("%s %s" % (user_data['first_name'], user_data['last_name']))
            account = account.replace('-', '_')[0:30]
        # Filter all non-word characters from account name
        account = re.sub('\W', '', account)[0:30]
        try:
            User.objects.get(username=account)
            account = None
        except User.DoesNotExist:
            pass
        form = RegistrationForm(initial={'username': account})

    args = {}
    args['fb_portrait'] = fb_data['portrait']
    args['fb_data'] = fb_data['info']
    args['form'] = form

    return render_to_response("facebook/register_form.html", args,
                              context_instance=RequestContext(request))

def connect(request):
    fb_user = get_user_from_cookie(request.COOKIES)
    if not fb_user:
        url = reverse('login')
	return redirect_with_next(request, url)

    profile = get_profile_by_fb_id(fb_user['uid'])
    if profile:
        user = profile.user
        if not user.is_active:
            return redirect_with_next(request, url) #FIXME
        user = authenticate(facebook_id=fb_user['uid'])
        # user should never be None
        login(request, user)
        return HttpResponseRedirect(request.REQUEST.get('next', '/'))

    # args = {}
    # return render_to_response('facebook/connect.html', args,
    #                          context_instance=RequestContext(request))

    url = reverse('facebook_register_form')
    return redirect_with_next(request, url)

