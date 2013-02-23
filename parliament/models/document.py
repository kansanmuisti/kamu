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

    version = models.CharField(max_length=10, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    error = models.CharField(max_length=50, blank=True, null=True)

    related_docs = models.ManyToManyField("self")
    keywords = models.ManyToManyField(Keyword)

    def save(self, *args, **kwargs):
        if not self.url_name:
            # only do this with the first save
            s = "%s %s" % (self.type, self.name)
            s = s.replace('/', '-')
            self.url_name = slugify(s)
        super(Document, self).save(*args, **kwargs)
    def __unicode__(self):
        return "%s %s" % (self.type, self.name)

    class Meta:
        app_label = 'parliament'
        unique_together = (('type', 'name'),)
        ordering = ('date',)

class DocumentProcessingStage(models.Model):
    STAGE_CHOICES = (
        ('intro', 'Introduced'),
        ('debate', 'Debate'),
        ('agenda', 'Agenda'),
        ('1stread', 'First reading'),
        ('2ndread', 'Second reading'),
        ('3rdread', 'Third reading'),
        ('finished', 'Finished'),
        ('onlyread', 'Only reading'),
        ('only2read', 'Only and 2nd reading'),
        ('only3read', 'Only and 3rd reading'),
        ('cancelled', 'Cancelled'),
        ('lapsed', 'Lapsed'),
        ('suspended', 'Suspended'),
    )

    doc = models.ForeignKey(Document, db_index=True)
    index = models.PositiveSmallIntegerField()
    stage = models.CharField(max_length=15, choices=STAGE_CHOICES, db_index=True)
    date = models.DateField()

    class Meta:
        app_label = 'parliament'
        unique_together = (('doc', 'stage'), ('doc', 'index'))

class DocumentSignature(models.Model):
    doc = models.ForeignKey('Document', db_index=True)
    member = models.ForeignKey('Member', db_index=True)
    date = models.DateField()

    class Meta:
        app_label = 'parliament'
        unique_together = (('doc', 'member'),)
