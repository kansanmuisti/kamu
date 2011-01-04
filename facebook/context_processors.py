from django.conf import settings
from django.utils import translation
from django.contrib.sites.models import Site

def facebook(request):
    """
    Returns context variables related to Facebook functionality.
    """
    fb_ctx = {}
    site = Site.objects.get_current()
    fb_ctx = {'fb_host': site.domain}

    if not settings.FACEBOOK_ENABLED:
        fb_ctx['fb_enabled'] = False
        return fb_ctx

    fb_ctx['fb_enabled'] = True
    lang_code = translation.get_language()
    if lang_code == 'fi':
        fb_ctx['fb_js_lang'] = 'fi_FI'
    else:
        fb_ctx['fb_js_lang'] = 'en_US'
    fb_ctx['fb_app_id'] = settings.FACEBOOK_APP_ID
    return fb_ctx
