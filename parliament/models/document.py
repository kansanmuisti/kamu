from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

class Keyword(models.Model):
    name = models.CharField(max_length=128, db_index=True, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'parliament'

class Document(models.Model):
    type = models.CharField(max_length=5, db_index=True)
    name = models.CharField(max_length=20, db_index=True)
    url_name = models.SlugField(max_length=20, unique=True)
    date = models.DateField(blank=True, null=True)
    info_link = models.URLField(blank=True, null=True)
    sgml_link = models.URLField(blank=True, null=True)
    subject = models.TextField()
    summary = models.TextField(blank=True, null=True)

    related_docs = models.ManyToManyField("self")
    keywords = models.ManyToManyField(Keyword)

    def save(self, *args, **kwargs):
        if not self.url_name:
            # only do this with the first save
            self.url_name = slugify("%s %s" % (self.type, self.name))
        super(Document, self).save(*args, **kwargs)
    def __unicode__(self):
        return "%s %s" % (self.type, self.name)

    class Meta:
        app_label = 'parliament'
        unique_together = (('type', 'id'),)
        ordering = ('date',)
