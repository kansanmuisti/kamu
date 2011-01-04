from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query_utils import Q
from django.contrib.csrf.middleware import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from kamu.users.models import KamuProfile
from facebook.api import get_user_from_cookie, do_request, FacebookError
from facebook.api import delete_cookie
from PIL import Image
import StringIO
import os
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
    if next and not next.beginswith(request.path):
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

@csrf_exempt
def register(request):
    if request.method != 'POST' or not 'signed_request' in request.POST:
        return HttpResponseBadRequest()

    (sig, payload) = request.POST['signed_request'].split('.')
    sig = base64_url_decode(sig)
    data = json.loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
        log.error('Unknown hash algorithm')
        return HttpResponseBadRequest()
    expected_sig = hmac.new(settings.FACEBOOK_APP_SECRET, msg=payload,
                            digestmod=hashlib.sha256).digest()
    if sig != expected_sig:
        log.error('Signature mismatch')
        return HttpResponseBadRequest()

    profile = get_profile_by_fb_id(data['user_id'])
    if profile:
        return HttpResponseForbidden() #FIXME

    reg = data['registration']

    # FIXME: save reg into session, display a page for choosing the user name

    user = User.objects.create_user(reg['name'], reg['email']) #FIXME
    user.first_name = reg['first_name']
    user.last_name = reg['last_name']
    user.save()

    profile_model = settings.AUTH_PROFILE_MODULE.split('.')[-1]
    profile_class = ContentType.objects.get(model=profile_model.lower()).model_class()
    profile = profile_class()
    profile.user = user
    profile.facebook_id = data['user_id']
    profile.location = reg['location']['name']
    bd = reg['birthday'].split('/')
    profile.birthday = '-'.join((bd[2], bd[0], bd[1]))
    profile.save()

    return HttpResponse()

'''
    uid = user['uid']
    try:
        resp = do_request(user['access_token'], uid)
    except FacebookError as e:
        if e.type == "OAuthException":
            url = reverse('login')
            resp = redirect_with_next(request, url)
            delete_cookie(resp)
            return resp
        else:
            raise
#    pprint.pprint(resp)
    me = resp

    picture = do_request(user['access_token'], uid + "/picture", raw=True)
    im = Image.open(StringIO.StringIO(picture))
    if im.size != (50, 50):
        raise Exception("Invalid image")
    if 'fb_portrait' in request.session:
        fn = os.path.join(settings.MEDIA_ROOT, request.session['fb_portrait'])
        tmpf = (os.open(fn, os.O_WRONLY), fn)
    else:
        dir = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP_DIR)
        tmpf = tempfile.mkstemp(suffix='.png', dir=dir)
        os.chmod(tmpf[1], 0644)
    path = os.path.join(settings.MEDIA_TMP_DIR, os.path.basename(tmpf[1]))

    file = os.fdopen(tmpf[0], "w")
    im.save(file, "png")
    file.close()

    request.session['fb_portrait'] = path
    print me
    args = {'info': me, 'portrait': path}
'''

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

    args = {}
    return render_to_response('facebook_connect.html', args,
                              context_instance=RequestContext(request))
