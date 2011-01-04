from django.contrib.auth import models, backends
from facebook.views import get_profile_by_fb_id

class FacebookBackend(backends.ModelBackend):
    def authenticate(self, facebook_id=None):
        if not facebook_id:
            return None

        profile = get_profile_by_fb_id(facebook_id)
        if profile:
            return profile.user
