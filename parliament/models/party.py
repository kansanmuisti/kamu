from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

class Party(models.Model):
    name = models.CharField(max_length=10, unique=True, db_index=True)
    full_name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='images/parties')
    homepage_link = models.URLField()
    # Unique color for visualizations, in the RGB #xxyyzz form
    vis_color = models.CharField(max_length=15, blank=True, null=True)

    def __unicode__(self):
        return self.full_name

    class Meta:
        app_label = 'parliament'
