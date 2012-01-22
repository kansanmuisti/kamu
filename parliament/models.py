from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

class TermManager(models.Manager):
    def get_for_date(self, date):
        query = Q(begin__lte=date)
        query &= Q(end__isnull=True) | Q(end__gte=date)
        return self.get(query)
    def latest(self):
        return self.order_by('-begin')[0]
    def visible(self):
        return self.filter(visible=True)

class Term(models.Model):
    name = models.CharField(max_length=40)
    display_name = models.CharField(max_length=40)
    begin = models.DateField()
    end = models.DateField(blank=True, null=True)
    visible = models.BooleanField(default=True)

    objects = TermManager()

    class Meta:
        ordering = ('-begin', )

    def __unicode__(self):
        return self.name

class Party(models.Model):
    name = models.CharField(max_length=10, unique=True, db_index=True)
    full_name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='images/parties')
    homepage_link = models.URLField()
    # Unique color for visualizations, in the RGB #xxyyzz form
    vis_color = models.CharField(max_length=15, blank=True, null=True)

    def __unicode__(self):
        return self.full_name


class PlenarySessionManager(models.Manager):
    def between(self, begin = None, end = None):
        query = Q()
        if begin:
            query &= Q(date__gte=begin)
        if end:
            query &= Q(date__lte=end)
        return self.filter(query)

class PlenarySession(models.Model):
    name = models.CharField(max_length=20)
    term = models.ForeignKey(Term, db_index=True)
    date = models.DateField(db_index=True)
    info_link = models.URLField()
    url_name = models.SlugField(max_length=20, unique=True, db_index=True)
    origin_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    objects = PlenarySessionManager()

    class Meta:
        ordering = ('-date', )

    def __unicode__(self):
        return self.name

class PlenarySessionItem(models.Model):
    TYPES = (('agenda', 'Agenda item'),
             ('question', 'Question time'),
             ('budget', 'Budget proposal'),)

    plsess = models.ForeignKey(PlenarySession)
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=15, choices=TYPES)
    description = models.CharField(max_length=150)

    class Meta:
        unique_together = (('plsess', 'number'),)
        ordering = ('number', )
