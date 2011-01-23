from django.conf import settings

class SetDefaultLanguageMiddleware(object):
    """
    Set language to the project's default one if the user hasn't already
    chosen a language explicitly. If this middleware is put before the
    LocaleMiddleware it will effectively overrule the browser's
    Accept-Language header field.
    """

    def process_request(self, request):
        if hasattr(request, 'session'):
            request.session.setdefault('django_language',
                                       settings.LANGUAGE_CODE)
