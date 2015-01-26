from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from parliament.models.base import UpdatableModel

class Party(UpdatableModel):
    abbreviation = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='images/parties')
    homepage_link = models.URLField()
    # Unique color for visualizations, in the RGB #xxyyzz form
    vis_color = models.CharField(max_length=15, blank=True, null=True)

    def is_governing(self, date=None):
        """Returns a boolean status indicating if the party has been or is
        currently participating in the government

        date: date for which the method should return governing status, if not set,
              returns the status for current date
        """
        qs = Q(end=None)
        if date is not None:
            qs |= Q(end__gte=date)
            qs &= Q(begin__lte=date)
        return bool(self.governingparty_set.filter(qs))

    # To avoid recursive imports..
    def get_activity_objects(self):
        if not hasattr(self, 'activity_objects'):
            activity = models.get_model('parliament', 'MemberActivity')
            self.activity_objects = activity.objects

        return self.activity_objects

    def get_party_association_objects(self):
        if not hasattr(self, 'party_association_objects'):
            party_association = models.get_model('parliament', 'PartyAssociation')
            self.party_association_objects = party_association.objects

        return self.party_association_objects

    def get_activity_score(self, begin=None, end=None):
        MemberActivity = models.get_model('parliament', 'MemberActivity')
        activities = MemberActivity.objects.filter(member__party=self)
        if begin:
            activities = activities.filter(time__gte=begin)
        if end:
            activities = activities.filter(time__lte=end)
        number_of_members = self.member_set.current().count()
        activities = activities.aggregate(act=models.Sum('type__weight'))
        activity_score = activities['act']
        if activity_score is None:
            activity_score = 0
        if not number_of_members:
            return 0
        return activity_score/number_of_members

    def get_activity_count_set(self, **kwargs):
        activity_objects = self.get_activity_objects()
        return activity_objects.counts_for_party(self.id, **kwargs)

    def get_activity_score_set(self, **kwargs):
        activity_objects = self.get_activity_objects()
        party_association_objects = self.get_party_association_objects()
        act_set = activity_objects.scores_for_party(self.id, **kwargs)
        for act in act_set:
            act_time = act['activity_date']
            query = Q(begin__lte=act_time)
            query = query & (Q(end__gte=act_time) | Q(end__isnull=True))
            query = query & Q(party=self)
            member_count = party_association_objects.filter(query).count()
            act['score'] /= member_count

        return act_set

    def __unicode__(self):
        return self.name

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
        return u"%s %s - %s : %s" % (self.party, self.begin, self.end, self.government)


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
        return u"%s (%s - %s)" % (self.name, self.begin.year, endyear)
