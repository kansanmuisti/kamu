from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

class Committee(models.Model):
    name = models.CharField(max_length=100, unique=True)
    origin_id = models.CharField(max_length=20, unique=True)
    url_name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        app_label = 'parliament'
