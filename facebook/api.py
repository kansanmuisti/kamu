import cgi
import hashlib
import time
import urllib

from django.conf import settings
from django.utils import simplejson

class FacebookError(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message
        super(FacebookError, self).__init__()
    def __unicode__(self):
        return u'%s: %s' % (self.type, self.message)

def do_request(access_token, path, args=None, raw=False):
    if not args:
        args = {}
    args["access_token"] = access_token
    url = "https://graph.facebook.com/%s" % path
    if args:
        url += "?%s" % urllib.urlencode(args)
    file = urllib.urlopen(url)
    content = file.read()
    try:
        if not raw:
            response = simplejson.loads(content)
        else:
            response = content
    finally:
        file.close()
    if not raw and response.get("error"):
        err = response.get("error")
        raise FacebookError(err['type'], err['message'])
    return response

def get_user_from_cookie(cookies):
    """Parses the cookie set by the official Facebook JavaScript SDK.

cookies should be a dictionary-like object mapping cookie names to
cookie values.

If the user is logged in via Facebook, we return a dictionary with the
keys "uid" and "access_token". The former is the user's Facebook ID,
and the latter can be used to make authenticated requests to the Graph API.
If the user is not logged in, we return None.

Download the official Facebook JavaScript SDK at
http://github.com/facebook/connect-js/. Read more about Facebook
authentication at http://developers.facebook.com/docs/authentication/.
"""
    app_id = settings.FACEBOOK_APP_ID
    app_secret = settings.FACEBOOK_APP_SECRET
    cookie = cookies.get("fbs_" + app_id, "")
    if not cookie:
        return None
    args = dict((k, v[-1]) for k, v in cgi.parse_qs(cookie.strip('"')).items())
    payload = "".join(k + "=" + args[k] for k in sorted(args.keys())
                      if k != "sig")
    sig = hashlib.md5(payload + app_secret).hexdigest()
    expires = int(args["expires"])
    if sig == args.get("sig") and (expires == 0 or time.time() < expires):
        return args
    else:
        return None

def delete_cookie(response):
    app_id = settings.FACEBOOK_APP_ID
    cookie = "fbs_" + app_id
    if settings.FACEBOOK_DOMAIN:
        domain = ".%s" % settings.FACEBOOK_DOMAIN
    else:
        domain = None
    response.delete_cookie(cookie, domain=domain)
