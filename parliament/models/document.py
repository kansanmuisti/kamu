from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

class Keyword(models.Model):
    name = models.CharField(max_length=128, db_index=True, unique=True)

    # To avoid recursive imports..
    def get_activity_objects(self):
        if not hasattr(self, 'activity_objects'):
            activity = models.get_model('parliament', 'MemberActivity')
            self.activity_objects = activity.objects

        return self.activity_objects

    def get_activity_score_set(self, **kwargs):
        activity_objects = self.get_activity_objects()
        return activity_objects.scores_for_keyword(self.id, **kwargs)

    def __unicode__(self):
        return self.name

    def get_slug(self):
        name = self.name
        name = name.replace(' (hist.)', '')
        return slugify(name)

    class Meta:
        app_label = 'parliament'

class Document(models.Model):
    TYPES = (
        ('mp_prop', _('MP law proposal')),
        ('gov_bill', _('Government bill')),
        ('written_ques', _('Written question')),
        ('interpellation', _('Interpellation')),
    )
    PROCESSING_FLOW = {
        'mp_prop': ('intro', 'debate', 'committee', 'agenda', '1stread', '2ndread', 'finished'),
        'gov_bill': ('intro', 'debate', 'committee', 'agenda', '1stread', '2ndread', 'finished'),
        'written_ques': ('intro', 'ministry', 'finished'),
    }

    type = models.CharField(max_length=30, db_index=True, choices=TYPES)
    name = models.CharField(max_length=30, unique=True, db_index=True)
    origin_id = models.CharField(max_length=30, unique=True, db_index=True)
    url_name = models.SlugField(max_length=20, unique=True, db_index=True)
    date = models.DateField(blank=True, null=True)
    info_link = models.URLField(blank=True, null=True)
    sgml_link = models.URLField(blank=True, null=True)
    subject = models.TextField()
    summary = models.TextField(blank=True, null=True)
    author = models.ForeignKey('parliament.Member', null=True, db_index=True,
        help_text="Set if the document is authored by an MP")

    version = models.CharField(max_length=10, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    error = models.CharField(max_length=50, blank=True, null=True)

    related_docs = models.ManyToManyField("self")
    keywords = models.ManyToManyField(Keyword)

    def save(self, *args, **kwargs):
        if not self.url_name:
            # only do this with the first save
            s = self.name
            s = s.replace('/', '-')
            self.url_name = slugify(s)
        super(Document, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('parliament.views.show_document', (), {'slug': self.url_name})

    def __unicode__(self):
        return "%s %s" % (self.type, self.name)

    class Meta:
        app_label = 'parliament'
        unique_together = (('type', 'name'),)
        ordering = ('date',)

class DocumentProcessingStage(models.Model):
    STAGE_CHOICES = (
        ('intro', _('Introduced')),
        ('debate', _('Debate')),
        ('committee', _('In committee')),
        ('agenda', _('On agenda')),
        ('1stread', _('First reading')),
        ('2ndread', _('Second reading')),
        ('3rdread', _('Third reading')),
        ('finished', _('Finished')),
        ('onlyread', _('Only reading')),
        ('only2read', _('Only and 2nd reading')),
        ('only3read', _('Only and 3rd reading')),
        ('cancelled', _('Cancelled')),
        ('lapsed', _('Lapsed')),
        ('suspended', _('Suspended')),
        ('ministry', _('In ministry')),
    )

    doc = models.ForeignKey(Document, db_index=True)
    index = models.PositiveSmallIntegerField()
    stage = models.CharField(max_length=15, choices=STAGE_CHOICES, db_index=True)
    date = models.DateField()

    class Meta:
        app_label = 'parliament'
        unique_together = (('doc', 'stage'), ('doc', 'index'))
        ordering = ('doc', 'index')

class DocumentSignature(models.Model):
    doc = models.ForeignKey('Document', db_index=True)
    member = models.ForeignKey('Member', db_index=True)
    date = models.DateField()

    class Meta:
        app_label = 'parliament'
        unique_together = (('doc', 'member'),)
