from django.conf import settings
from django.utils import translation
from django.conf import settings

def other_languages(request):
    cur_lang = translation.get_language()
    langs=[l for l in settings.LANGUAGES_EXT if l[0] != cur_lang]
    return { 'OTHER_LANGUAGES': langs }
