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

    def is_currently_governing(self):
        return bool(self.governingparty_set.filter(end__exact=None))

    # To avoid recursive imports..
    def get_activity_objects(self):
        if not hasattr(self, 'activity_objects'):
            activity = models.get_model('parliament', 'MemberActivity')
            self.activity_objects = activity.objects

        return self.activity_objects

    def get_activity_count_set(self, resolution=None):
        activity_objects = self.get_activity_objects()
        return activity_objects.counts_for_party(self.id)
 
    def get_activity_score_set(self, resolution=None):
        activity_objects = self.get_activity_objects()
        return activity_objects.scores_for_party(self.id)
 
    def __unicode__(self):
        return self.full_name

    class Meta:
        app_label = 'parliament'

class GoverningParty(models.Model):
    """ Keeps track when the party has been in the government """
    party = models.ForeignKey(Party, db_index=True)
    begin = models.DateField(help_text="Beginning of government participation")
    end = models.DateField(null=True, help_text="End of government participation")
    government = models.ForeignKey("Government", help_text="Government wherein the party participated")
    class Meta:
        app_label = 'parliament'

    def __unicode__(self):
        return u"%s %s - %s : %s" % (self.party,self.begin,self.end,self.government)

class Government(models.Model):
    """ Governments of the nation on timeline """
    begin = models.DateField(help_text="Date when the government began operations")
    end = models.DateField(null=True, help_text="End date for the government")
    name = models.CharField(max_length=50, help_text="Descriptive name for this government, depends on national custom")
    
    class Meta:
        app_label = 'parliament'

    def __unicode__(self):
        if self.end:
            endyear = self.end.year
        else:
            endyear = None
        return u"%s (%s - %s)" % (self.name,self.begin.year,endyear)
