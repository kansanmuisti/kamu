from django.db import models, connection
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import pgettext_lazy as pgettext, ugettext_lazy as _
from django import VERSION as DJANGO_VERSION

from parliament.models.committee import *
from parliament.models.party import *
from parliament.models.session import *
from parliament.models.document import Keyword
from parliament.models.base import UpdatableModel

import datetime

# Django bug workaround (only in version < 1.7)
if DJANGO_VERSION[0:2] < (1, 7):
    from django.db.models.loading import cache as model_cache

    if not model_cache.loaded:
        model_cache._populate()

# Helper to filter Association objects
class AssociationQuerySet(models.query.QuerySet):
    def current(self):
        return self.filter(end__isnull=True)

class AssociationManager(models.Manager):
    def current(self):
        return self.get_query_set().current()
    def get_query_set(self):
        return AssociationQuerySet(self.model, using=self._db)


class MemberManager(models.Manager):
    def current(self):
        """Currently serving MPs"""
        mem_list = PartyAssociation.objects.filter(end__isnull=True).distinct().values_list('member', flat=True)
        return self.filter(id__in=mem_list)

    def active_in(self, date_begin, date_end):
        """MPs that have served between date_begin and date_end"""
        query = Q()
        if date_end:
            query &= Q(begin__lte=date_end)
        query &= Q(end__isnull=True) | Q(end__gte=date_begin)
        mem_list = PartyAssociation.objects.filter(query).distinct().values_list('member', flat=True)
        return self.filter(id__in=mem_list)
    def active_in_term(self, term):
        """MPs that have served during given parliamentary Term"""
        return self.active_in(term.begin, term.end)
    def in_district(self, district, date_begin, date_end):
        """MPs from given District that have served between date_begin and date_end"""
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

class Member(UpdatableModel):
    """
    Member of parliament. Can be current or past.
    """
    name = models.CharField(max_length=50, unique=True)
    origin_id = models.CharField(max_length=20, unique=True, db_index=True, blank=True, null=True)
    url_name = models.SlugField(max_length=50, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=50, null=True, blank=True)
    given_names = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, null=True, blank=True)
    surname = models.CharField(max_length=50)
    summary = models.TextField(null=True)

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

    __export_stats_fields = ('attendance', 'party_agree', 'session_agree')
    def get_latest_stats(self):
        try:
            latest = self.memberstats_set.order_by('-begin')[0]
        except IndexError:
            return {k: 0.0 for k in self.__export_stats_fields}

        latest.calc()
        latest = {k: getattr(latest, k) for k in self.__export_stats_fields}
        return latest

    def get_activity_score(self, begin=None, end=None):
        activities = self.memberactivity_set
        if begin: activities = activities.filter(time__gte=begin)
        if end: activities = activities.filter(time__lte=end)

        act = activities.aggregate(act=models.Sum('type__weight'))['act']
        if not act: act = 0.0
        return act

    def get_activity_count_set(self, **kwargs):
        return MemberActivity.objects.counts_for_member(self.id, **kwargs)

    def get_activity_score_set(self, **kwargs):
        return MemberActivity.objects.scores_for_member(self.id, **kwargs)

    def get_activity_counts(self, **kwargs):
        act = self.get_activity_count_set(**kwargs)

        return list(act)

    def get_terms(self):
        da_list = self.districtassociation_set.order_by('begin')
        first_da = da_list[0]
        term_filter = Q(begin__gte=first_da.begin) | Q(end__isnull=True)
        term_list = list(Term.objects.filter(term_filter).order_by('begin'))
        for term in term_list:
            term.found = False
        for da in da_list:
            for term in term_list:
                if term.found:
                    continue
                if term.end is not None and term.end < da.begin:
                    continue
                if da.end is not None and term.begin > da.end:
                    continue
                term.found = True

        return filter(lambda x: x.found, term_list)

    def get_age(self):
        born = self.birth_date
        today = datetime.date.today()
        try: 
            birthday = born.replace(year=today.year)
        except ValueError: # raised when birth date is February 29 and the current year is not a leap year
            birthday = born.replace(year=today.year, day=born.day-1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year

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

    def get_latest_district(self):
        latest = self.districtassociation_set.order_by('-begin')[0]
        return latest

    def get_posts(self, current=True):
        posts = {}
        qs = CommitteeAssociation.objects.filter(member=self)
        if current:
            qs = qs.current()
        l = list(qs.in_print_order())
        posts['committee'] = l

        qs = self.ministryassociation_set.all()
        if current:
            qs = qs.current()
        posts['ministry'] = list(qs.order_by('begin'))

        qs = self.speakerassociation_set.all()
        if current:
            qs = qs.current()
        posts['speaker'] = list(qs.order_by('begin'))

        return posts

    @models.permalink
    def get_absolute_url(self):
        return ('parliament.views.show_member', (), {'member': self.url_name})

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

    def __unicode__(self):
        if self.district:
            name = self.district.name
        else:
            name = self.name
        return u"%s in district %s %s - %s" % (self.member, name, self.begin, self.end)

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

class CommitteeAssociationManager(AssociationManager):
    class QuerySet(AssociationQuerySet):
        def in_print_order(self):
            def key(ca):
                if not ca.role:
                    role = 'member'
                else:
                    role = ca.role
                role_orders = {'deputy-m': 3, 'member': 2, 'deputy-cm': 1, 'chairman': 0}
                # Sort on role first, then on committee name.
                return "%d-%s" % (role_orders[role], ca.committee.name)
            qs = self.select_related('committee')
            return sorted(qs, key=key)

    def get_query_set(self):
        return CommitteeAssociationManager.QuerySet(self.model, using=self._db)

class CommitteeAssociation(models.Model):
    ROLE_CHOICES = (
        ('chairman', _('Chairman')),
        ('deputy-cm', _('Deputy Chairman')),
        ('member', pgettext('organisation', 'Member')),
        ('deputy-m', _('Deputy Member')),
    )
    member = models.ForeignKey(Member, db_index=True)
    committee = models.ForeignKey(Committee)
    begin = models.DateField()
    end = models.DateField(db_index=True, blank=True, null=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, null=True)

    objects = CommitteeAssociationManager()

    class Meta:
        app_label = 'parliament'

    def __unicode__(self):
        if not self.role:
            role = 'member'
        else:
            role = self.role
        return u"%s %s in %s from %s to %s" % (self.member, role, self.committee, self.begin, self.end)

class SpeakerAssociation(models.Model):
    ROLE_CHOICES = (
        ('speaker', _('Speaker')),
        ('1st-deputy-speaker', _('1st Deputy Speaker')),
        ('2nd-deputy-speaker', _('2st Deputy Speaker')),
    )
    member = models.ForeignKey(Member, db_index=True)
    begin = models.DateField()
    end = models.DateField(db_index=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text='Speaker position')

    objects = AssociationManager()

    class Meta:
        app_label = 'parliament'

    def __unicode__(self):
        return u"%s (%s) from %s to %s" % (self.member, self.role, self.begin, self.end)


class MinistryAssociation(models.Model):
    ROLE_CHOICES = (
        ('minister', _('Minister')),
    )
    member = models.ForeignKey(Member, db_index=True)
    begin = models.DateField()
    end = models.DateField(db_index=True, blank=True, null=True)
    label = models.CharField(max_length=50, help_text='Official descriptive name of the position. eg. minister of of International Development')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text='Position of the official. eg. minister.')

    objects = AssociationManager()

    class Meta:
        app_label = 'parliament'

    def __unicode__(self):
        return u"%s %s (%s) from %s to %s" % (self.member, self.label, self.role, self.begin, self.end)

class MemberActivityManager(models.Manager):
    def during(self, begin, end):
        query = Q()
        if end:
            query &= Q(time__lte=end)
        if begin:
            query &= Q(time__gte=begin)
        return self.filter(query)
    def during_term(self, term):
        return self.during(term.begin, term.end)

    def aggregates(self, **kwargs):
        act = self

        since = kwargs.get('since')
        until = kwargs.get('until')
        resolution = kwargs.get('resolution')
        if since:
            act = act.filter(time__gte=since)
        if until:
            act = act.filter(time__lte=until)
        if resolution:
            truncate_date = connection.ops.date_trunc_sql(resolution, 'time')
            act = act.extra({'activity_date': truncate_date})
        else:
            act = act.extra({'activity_date': 'date(time)'})
        act = act.values('activity_date', 'type')
        act = act.order_by('activity_date', 'type')

        return act

    def get_score_set(self, qfilter=Q(), **kwargs):
        if 'keyword' in kwargs:
            qfilter &= Q(keywordactivity__keyword=kwargs['keyword'])

        act = self.aggregates(**kwargs)
        act = act.filter(qfilter)

        return act.annotate(score=models.Sum('type__weight'))

    def get_count_set(self, qfilter=Q(), **kwargs):
        act = self.aggregates(**kwargs)
        act = act.filter(qfilter)

        return act.annotate(count=models.Count('id'))

    def scores_for_party(self, party, **kwargs):
        qs = Q(member__party=party)
        if 'keyword' in kwargs:
            qs &= Q(keywordactivity__keyword=kwargs['keyword'])
        return self.get_score_set(qs, **kwargs)

    def scores_for_member(self, member, **kwargs):
        return self.get_score_set(Q(member=member), **kwargs)

    def scores_for_keyword(self, keyword, **kwargs):
        return self.get_score_set(Q(keywordactivity__keyword=keyword), **kwargs)

    def counts_for_party(self, party, **kwargs):
        return self.get_count_set(Q(member__party=party), **kwargs)

    def counts_for_member(self, member, **kwargs):
        return self.get_count_set(Q(member=member), **kwargs)

class MemberActivityType(models.Model):
    type = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=50)
    weight = models.FloatField()

    def __unicode__(self):
        return u"%s: %s (weight %d)" % (self.type, self.name, self.weight)

    class Meta:
        app_label = 'parliament'


class MemberActivity(models.Model):
    # If member is None, it is activity related to a government bill.
    member = models.ForeignKey(Member, db_index=True, null=True)
    time = models.DateTimeField(db_index=True)
    type = models.ForeignKey(MemberActivityType, db_index=True)

    objects = MemberActivityManager()

    def get_keywords(self):
        return None

    def update_keyword_activities(self):
        current_keywords = self.keywordactivity_set.all()
        kwa_dict = {}
        for kwa in current_keywords:
            kwa_dict[kwa.keyword.id] = kwa
            kwa.found = False
        # First add the new keywords
        new_keywords = self.get_keywords()
        if new_keywords:
            for kw in new_keywords:
                if kw.id in kwa_dict:
                    kwa_dict[kw.id].found = True
                else:
                    kwa = KeywordActivity(keyword=kw, activity=self)
                    # print "add %s" % unicode(kwa).encode('utf8')
                    kwa.save()
        # Then remove the deleted keywords.
        for kw_id in kwa_dict:
            if not kwa_dict[kw_id].found:
                kwa = kwa_dict[kw_id]
                # print u"remove %s" % unicode(kwa).encode('utf8')
                kwa.delete()

    def get_target_info(self):
        d = {}
        target = {}
        acttype = self.type.pk
        if acttype in ('FB', 'TW'):
            o = self.socialupdateactivity.update
            target['text'] = o.text
            target['url'] = o.get_origin_url()
        elif acttype == 'ST':
            o = self.statementactivity.statement
            target['text'] = o.text
            target['url'] = o.get_indocument_url()
        elif acttype in ('IN', 'WQ', 'GB', 'SI'):
            if acttype == 'SI':
                o = self.signatureactivity.signature.doc
            else:
                o = self.initiativeactivity.doc
            target['text'] = o.summary
            target['subject'] = o.subject
            target['name'] = o.name
            target['type'] = o.type
            target['url'] = o.get_absolute_url()

            keywords = [{'id': kw.id, 'name': kw.name, 'slug': kw.get_slug()} for kw in o.keywords.all()]
            target['keywords'] = keywords
        else:
            raise Exception("Invalid type %s" % acttype)

        target['object'] = o
        return target

    def save(self, *args, **kwargs):
        ret = super(MemberActivity, self).save(*args, **kwargs)
        self.update_keyword_activities()
        return ret

    def __unicode__(self):
        return u"%s: %s: %s" % (self.time, self.type, unicode(self.member))

    class Meta:
        app_label = 'parliament'
        ordering = ('time', 'member__name')


class KeywordActivity(models.Model):
    activity = models.ForeignKey(MemberActivity, db_index=True)
    keyword = models.ForeignKey(Keyword, db_index=True)

    def __unicode__(self):
        kw = unicode(self.keyword)
        act = unicode(self.activity)
        return u"Activity on %s: %s" % (kw, act)

    class Meta:
        app_label = 'parliament'
        unique_together = (('activity', 'keyword'),)

class InitiativeActivity(MemberActivity):
    # This is both for written questions and law proposals.

    doc = models.ForeignKey(Document, db_index=True)

    objects = MemberActivityManager()

    def get_keywords(self):
        return self.doc.keywords.all()

    def save(self, *args, **kwargs):
        doc = self.doc
        assert doc.type in ('mp_prop', 'written_ques', 'gov_bill'), "Invalid document type: %s" % doc
        if doc.type != 'gov_bill':
            assert doc.author is not None, "Document has no author: %s" % doc
        if doc.type == 'mp_prop':
            self.type = MemberActivityType.objects.get(type='IN')
        elif doc.type == 'written_ques':
            self.type = MemberActivityType.objects.get(type='WQ')
        else:
            self.type = MemberActivityType.objects.get(type='GB')
        if doc.type != 'gov_bill':
            self.member = self.doc.author
        else:
            self.member = None
        self.time = self.doc.date
        return super(InitiativeActivity, self).save(*args, **kwargs)

    def __unicode__(self):
        s = super(InitiativeActivity, self).__unicode__()
        return "%s: %s" % (s, self.doc)

    class Meta:
        app_label = 'parliament'

class RebelVoteActivity(MemberActivity):
    TYPE = 'RV'
    vote = models.ForeignKey(Vote, unique=True)

    objects = MemberActivityManager()

    def save(self, *args, **kwargs):
        self.type = self.TYPE
        return super(RebelVoteActivity, self).save(*args, **kwargs)

    class Meta:
        app_label = 'parliament'

class CommitteeDissentActivity(MemberActivity):
    TYPE = 'CD'
    doc = models.ForeignKey(Document, db_index=True)

    objects = MemberActivityManager()

    def save(self, *args, **kwargs):
        self.type = MemberActivityType.objects.get(type=self.TYPE)
        return super(CommitteeDissentActivity, self).save(*args, **kwargs)

    def __unicode__(self):
        s = super(CommitteeDissentActivity, self).__unicode__()
        return "%s: %s" % (s, self.doc)

    class Meta:
        app_label = 'parliament'

from social.models import Feed, Update

class MemberSocialFeed(Feed):
    member = models.ForeignKey(Member, db_index=True)
    class Meta:
        app_label = 'parliament'

class SocialUpdateActivity(MemberActivity):
    update = models.ForeignKey(Update, unique=True)

    objects = MemberActivityManager()

    def save(self, *args, **kwargs):
        self.type = MemberActivityType.objects.get(type=self.update.feed.type)
        mf = self.update.feed.membersocialfeed
        self.member = mf.member
        self.time = self.update.created_time
        return super(SocialUpdateActivity, self).save(*args, **kwargs)

    class Meta:
        app_label = 'parliament'

class StatementActivity(MemberActivity):
    TYPE = 'ST'
    statement = models.ForeignKey(Statement, unique=True)

    objects = MemberActivityManager()

    def get_keywords(self):
        docs = self.statement.item.docs.all()
        kw_dict = {}
        for doc in docs:
            for kw in doc.keywords.all():
                kw_dict[kw.id] = kw
        return kw_dict.values()

    def save(self, *args, **kwargs):
        self.type = MemberActivityType.objects.get(type=self.TYPE)
        self.member = self.statement.member
        self.time = self.statement.item.plsess.date
        return super(StatementActivity, self).save(*args, **kwargs)

    class Meta:
        app_label = 'parliament'

class SignatureActivity(MemberActivity):
    TYPE = 'SI'
    signature = models.ForeignKey(DocumentSignature, unique=True)

    objects = MemberActivityManager()

    def get_keywords(self):
        return self.signature.doc.keywords.all()

    def save(self, *args, **kwargs):
        self.type = MemberActivityType.objects.get(type=self.TYPE)
        self.member = self.signature.member
        self.time = self.signature.date
        return super(SignatureActivity, self).save(*args, **kwargs)

    class Meta:
        app_label = 'parliament'
