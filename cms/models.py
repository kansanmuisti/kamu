from django.db import models
from django.utils import translation
from django.conf import settings
from cms.markupfield.fields import MarkupField
from django.utils.translation import get_language
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

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
        if not lang:
            lang = get_language()
        # Case of no news
        try:
            latest = self.content_set.get(language=lang).revision_set.all()[0]
        except ObjectDoesNotExist:
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

        if amount == None:
            return newsitems
        else:
            return newsitems[:amount]

class Newsitem(Item):
    date = models.DateField()

    objects = NewsitemManager()

    class Meta:
        ordering = ['-date']

class Content(models.Model):
    item = models.ForeignKey(Item)
    language = models.CharField(max_length=10)

    # FIXME: Sanity check language

    def __unicode__(self):
        revision = self.revision_set.order_by('-date')
        if len(revision) > 0:
            return str(self.item.category) + " / " + str(revision[0])
        else:
            return str(self.item.category) + " / no revisions exist"

class Revision(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    content = models.ForeignKey(Content)
    subject = models.CharField(max_length=200, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    data = MarkupField()

    class Meta:
        ordering = ['-date']

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
