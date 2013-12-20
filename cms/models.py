from django.db import models
from django.utils import translation
from django.conf import settings
from cms.markupfield.fields import MarkupField
from django.utils.translation import get_language
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.forms import ModelForm

DEFAULT_LANGUAGE = settings.LANGUAGE_CODE

class Category(models.Model):
    name = models.CharField(max_length=80)

    def __unicode__(self):
        return self.name

class ItemManager(models.Manager):
    def retrieve(self, category):
        category = Category.objects.get(name=category)

        return self.get(category=category)

    def retrieve_content(self, category, lang=None):
        latest = self.retrieve(category=category).get_latest(lang)
        return latest

class Item(models.Model):
    category = models.ForeignKey(Category)

    objects = ItemManager()

    def get_latest(self, lang=None):
        if lang:
            explicit_language = True
        else:
            explicit_language = False
            lang = get_language()
        # Case of no news
        content_list = list(self.content_set.filter(language=lang))
        if not content_list and not explicit_language:
            content_list = list(self.content_set.filter(language=DEFAULT_LANGUAGE))
        if not content_list:
            return None
        assert len(content_list) == 1
        content = content_list[0]
        try:
            latest = content.revision_set.all()[0]
        except Content.DoesNotExist:
            return None
        return latest

    @property
    def content(self):
        return self.get_latest()

    def __unicode__(self):
        try:
            content = self.content_set.get(language=get_language())
        except Content.DoesNotExist:
            content = self.content_set.all()
            if not content:
                return "Content not set"
            content = content[0]

        return "Content in '%s': %s" % (content.language, str(content))

class NewsitemManager(models.Manager):
    def newest(self, amount=None, lang=None):
        if not lang:
            lang=get_language()
        newsitems = self.filter(content__language=lang)
        if not newsitems:
            newsitems = self.filter(content__language=DEFAULT_LANGUAGE)
        if amount == None:
            return newsitems
        else:
            return newsitems[:amount]

class Newsitem(Item):
    date = models.DateField()

    objects = NewsitemManager()

    @models.permalink
    def get_absolute_url(self):
        date = str(self.date).replace('-', '/')
        index = 1 # hardcode for now
        return ('cms.views.render_news', (), {'date': date, 'index': index})

    def __unicode__(self):
        return "News for %s" % self.date

    class Meta:
        ordering = ['-date']

class Content(models.Model):
    item = models.ForeignKey(Item)
    language = models.CharField(max_length=10)

    # FIXME: Sanity check language

    def get_latest_revision(self):
        latest = self.revision_set.all()[0:1]
        if not latest:
            return None
        return latest[0]

    def __unicode__(self):
        revision = self.revision_set.order_by('-date')
        if len(revision) > 0:
            return str(self.item.category) + " / " + str(revision[0])
        else:
            return str(self.item.category) + " / no revisions exist"

class Revision(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    summary = MarkupField(blank=True)
    content = models.ForeignKey(Content)
    subject = models.CharField(max_length=200, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    data = MarkupField(blank=True)

    class Meta:
        ordering = ['-date']

    def has_data(self):
        return bool(self.data.rendered)

    def __unicode__(self):
        if not self.subject:
            subject = "[No subject]"
        else:
            subject = self.subject
        return "%s / %s" % (str(self.date), subject)

# This exists to make things just a bit snappier (not used for now)
class Cache(models.Model):
    item = models.ForeignKey(Item)
    language = models.CharField(max_length=10)
    content = models.ForeignKey(Content)
    revision = models.ForeignKey(Revision)


class NewRevisionForm(ModelForm):
    class Meta:
        model = Revision
        exclude = ('content',)
