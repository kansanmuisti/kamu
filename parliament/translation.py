from modeltranslation.translator import translator, TranslationOptions
from parliament.models import Keyword

class KeywordTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Keyword, KeywordTranslationOptions)
