from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _


class Committee(models.Model):
    name = models.CharField(max_length=100, unique=True,
                            help_text='Name of the committee')
    description = models.CharField(max_length=500, null=True,
                                   help_text='Description of the committee')
    origin_id = models.CharField(max_length=20, unique=True, null=True,
                                 help_text='Upstream identifier (in URL)')
    current = models.BooleanField(help_text='Is the committee current or past')
    url_name = models.CharField(max_length=100, unique=True, null=True,
                                help_text='Name identifier for URLs')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        app_label = 'parliament'

    def save(self, *args, **kwargs):
        if not self.url_name:
            # only do this with the first save
            self.url_name = slugify(self.name)
        super(Committee, self).save(*args, **kwargs)
