from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from parliament.models.party import *
from parliament.models.session import *

class MemberManager(models.Manager):
    def active_in(self, date_begin, date_end):
        query = Q()
        if date_end:
            query &= Q(begin__lte=date_end)
        query &= Q(end__isnull=True) | Q(end__gte=date_begin)
        mem_list = PartyAssociation.objects.filter(query).distinct().values_list('member', flat=True)
        return self.filter(id__in=mem_list)
    def active_in_term(self, term):
        return self.active_in(term.begin, term.end)
    def in_district(self, district, date_begin, date_end):
        query = Q(name = district)
        if date_end:
            query &= Q(begin__lte=date_end)
        query &= Q(end__isnull=True) | Q(end__gte=date_begin)
        mem_list = DistrictAssociation.objects.filter(query).distinct().values_list('member', flat=True)
        return self.filter(id__in=mem_list)
    def get_with_print_name(self, name):
        names = name.split()
        names = list((names[-1],)) + names[0:-1]
        name = ' '.join(names)
        return self.get(name=name)

class Member(models.Model):
    name = models.CharField(max_length=50, unique=True)
    origin_id = models.CharField(max_length=20, unique=True, db_index=True, blank=True, null=True)
    url_name = models.SlugField(max_length=50, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=50, null=True, blank=True)
    given_names = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)

    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    party = models.ForeignKey(Party, blank=True, null=True)
    photo = models.ImageField(upload_to='images/members')
    info_link = models.URLField()
    wikipedia_link = models.URLField(blank=True, null=True)
    homepage_link = models.URLField(blank=True, null=True)

    objects = MemberManager()

    def get_stats(self, begin, end):
        try:
            ms = MemberStats.objects.for_period(begin, end).get(member = self)
        except MemberStats.DoesNotExist:
            return None
        ms.calc()
        return ms

    def save(self, *args, **kwargs):
        if not self.url_name:
            # only do this with the first save
            self.url_name = slugify(self.name)
        super(Member, self).save(*args, **kwargs)

    def get_print_name(self):
        names = self.name.split()
        names = list(names[1:]) + names[0:1]
        name = ' '.join(names)
        return name

    @models.permalink
    def get_absolute_url(self):
        return ('votes.views.show_member', (), {'member': self.url_name})

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'parliament'


class MemberStatsManager(models.Manager):
    def between(self, date_begin, date_end):
        query = Q()
        if date_end:
            query &= Q(begin__lte=date_end)
        if date_begin:
            query &= Q(end__isnull=True) | Q(end__gte=date_begin)
        return self.filter(query)
    def for_period(self, date_begin, date_end):
        return self.filter(begin=date_begin, end=date_end)

class MemberStats(models.Model):
    member = models.ForeignKey(Member)
    begin = models.DateField()
    end = models.DateField(blank = True, null = True)

    attendance = None
    party_agree = None
    session_agree = None

    # <agree>,<disagree>
    party_agreement = models.CommaSeparatedIntegerField(max_length = 20)
    session_agreement = models.CommaSeparatedIntegerField(max_length = 20)
    vote_counts = models.CommaSeparatedIntegerField(max_length = 30)
    statement_count = models.IntegerField()
    election_budget = models.DecimalField(max_digits=10, decimal_places=2,
                                          blank=True, null=True)

    objects = MemberStatsManager()

    def __calc_attendance(self):
        vc = self.vote_counts.split(',')
        vcnt = {}
        # Clumsy... must be a better way
        for v in Vote.VOTE_CHOICES:
            vcnt[v[0]] = int(vc[Vote.VOTE_CHOICES.index(v)])
        return float(vcnt['Y'] + vcnt['N']) / (vcnt['Y'] + vcnt['N'] + vcnt['E'] + vcnt['A'])

    def __calc_agree(self, agr):
        n = agr.split(',')
        n = (int(n[0]), int(n[1]))
        if (n[0] + n[1] == 0):
            return float(0)     # FIXME
        return float(n[0]) / (n[0] + n[1])

    def calc(self):
        if not self.vote_counts:
            return
        self.attendance = self.__calc_attendance()
        self.party_agree = self.__calc_agree(self.party_agreement)
        self.session_agree = self.__calc_agree(self.session_agreement)

    class Meta:
        app_label = 'parliament'

class TermMember(models.Model):
    term = models.ForeignKey(Term)
    member = models.ForeignKey(Member)
    election_budget = models.DecimalField(max_digits=10, decimal_places=2,
                                          blank=True, null=True)
    class Meta:
        app_label = 'parliament'

class Seat(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField() # "column"
    x = models.FloatField()
    y = models.FloatField()

    def __unicode__(self):
        return "%d/%d" % (self.row, self.seat)

    class Meta:
        unique_together = (('row', 'seat'),)
        app_label = 'parliament'

class MemberSeatManager(models.Manager):
    def for_date(self, date):
        query = Q(begin__lte=date)
        query &= Q(end__isnull=True) | Q(end__gte=date)
        return self.filter(query)

class MemberSeat(models.Model):
    seat = models.ForeignKey(Seat)
    member = models.ForeignKey(Member, db_index=True)
    begin = models.DateField()
    end = models.DateField(blank=True, null=True)

    objects = MemberSeatManager()

    def __unicode__(self):
        args = (str(self.seat), self.begin, self.end, str(self.member))
        return "%s (%s..%s): %s" % args
    class Meta:
        unique_together = (('member', 'begin', 'end'), ('seat', 'begin', 'end'))
        app_label = 'parliament'

class District(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    long_name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label = 'parliament'

class DistrictAssociationManager(models.Manager):
    def between(self, date_begin, date_end):
        query = Q()
        if date_end:
            query &= Q(begin__lte=date_end)
        if date_begin:
            query &= Q(end__isnull=True) | Q(end__gte=date_begin)
        return self.filter(query)
    def for_member_in_term(self, mp, term):
        return self.between(term.begin, term.end).filter(member=mp)
    def list_between(self, date_begin, date_end):
        return self.between(date_begin, date_end).order_by('name').values_list('name', flat=True).distinct()

class DistrictAssociation(models.Model):
    member = models.ForeignKey(Member, db_index=True)
    # either district or name must be defined
    district = models.ForeignKey(District, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    begin = models.DateField()
    end = models.DateField(blank=True, null=True)

    objects = DistrictAssociationManager()

    class Meta:
        app_label = 'parliament'
        unique_together = (('member', 'begin'),)

class PartyAssociation(models.Model):
    member = models.ForeignKey(Member, db_index=True)
    # either party or name must be defined
    party = models.ForeignKey(Party, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    begin = models.DateField()
    end = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'parliament'

class MemberActivityManager(models.Manager):
    def during(self, begin, end):
        query = Q()
        if end:
            query &= Q(date__lte=end)
        if begin:
            query &= Q(date__gte=begin)
        return self.filter(query)
    def during_term(self, term):
        return self.during(term.begin, term.end)

class MemberActivity(models.Model):
    TYPES = [
        ('IN', 'Initiative'),
        ('RV', 'Rebel vote'),
        ('CD', 'Committee dissent'),
    ]
    WEIGHTS = {'IN': 100, 'RV': 10, 'CD': 20}

    member = models.ForeignKey(Member, db_index=True)
    date = models.DateField(db_index=True)
    weight = models.PositiveIntegerField()
    type = models.CharField(max_length=5, db_index=True)

    objects = MemberActivityManager()

    def __unicode__(self):
        return "%s: %s: %s" % (self.date, self.type, self.member)

    class Meta:
        ordering = ('date', 'member__name')

class InitiativeActivity(MemberActivity):
    TYPE = 'IN'
    doc = models.ForeignKey(Document, db_index=True)

    objects = MemberActivityManager()

    def save(self, *args, **kwargs):
        self.type = self.TYPE
        if not self.weight:
            self.weight = self.WEIGHTS[self.type]
        super(InitiativeActivity, self).save(*args, **kwargs)

    def __unicode__(self):
        s = super(InitiativeActivity, self).__unicode__()
        return "%s: %s" % (s, self.doc)

    class Meta:
        app_label = 'parliament'

#class RebelVoteActivity(MemberActivity):
#    session = models.ForeignKey(Session)

class CommitteeDissentActivity(MemberActivity):
    TYPE = 'CD'
    doc = models.ForeignKey(Document, db_index=True)

    objects = MemberActivityManager()

    def save(self, *args, **kwargs):
        self.type = self.TYPE
        if not self.weight:
            self.weight = self.WEIGHTS[self.type]
        super(CommitteeDissentActivity, self).save(*args, **kwargs)

    def __unicode__(self):
        s = super(CommitteeDissentActivity, self).__unicode__()
        return "%s: %s" % (s, self.doc)

    class Meta:
        app_label = 'parliament'

from social.models import Feed

class MemberSocialFeed(Feed):
    member = models.ForeignKey(Member, db_index=True)

    class Meta:
        app_label = 'parliament'
