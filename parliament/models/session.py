from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from parliament.models.document import *
from parliament.models.member import *
from parliament.models.base import UpdatableModel

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

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('-begin', )
        app_label = 'parliament'

class PlenarySessionManager(models.Manager):
    def between(self, begin = None, end = None):
        query = Q()
        if begin:
            query &= Q(date__gte=begin)
        if end:
            query &= Q(date__lte=end)
        return self.filter(query)

class PlenarySession(UpdatableModel):
    name = models.CharField(max_length=20)
    term = models.ForeignKey(Term, db_index=True)
    date = models.DateField(db_index=True)
    info_link = models.URLField()
    url_name = models.SlugField(max_length=20, unique=True, db_index=True)
    origin_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    origin_version = models.CharField(max_length=10, null=True, blank=True)

    objects = PlenarySessionManager()

    class Meta:
        ordering = ('-date', )
        app_label = 'parliament'

    def __unicode__(self):
        return self.name

class PlenarySessionItem(models.Model):
    TYPES = (('agenda', _('Agenda item')),
             ('question', _('Question time')),
             ('budget', _('Budget proposal')),)

    plsess = models.ForeignKey(PlenarySession)
    number = models.PositiveIntegerField()
    sub_number = models.PositiveIntegerField(null=True, blank=True)
    type = models.CharField(max_length=15, choices=TYPES)
    description = models.CharField(max_length=1000)
    sub_description = models.CharField(max_length=100, null=True, blank=True)
    docs = models.ManyToManyField(Document, through='PlenarySessionItemDocument')
    processing_stage = models.CharField(max_length=20, null=True, blank=True, db_index=True)

    # cache the counts here for faster SELECTs
    nr_votes = models.IntegerField(null=True, blank=True, db_index=True)
    nr_statements = models.IntegerField(null=True, blank=True, db_index=True)

    class Meta:
        unique_together = (('plsess', 'number', 'sub_number'),)
        ordering = ('-plsess__date', '-number', '-sub_number')
        app_label = 'parliament'

    def count_related_objects(self):
        self.nr_votes = self.plenary_votes.count()
        self.nr_statements = self.statement_set.exclude(type='speaker').count()

    def get_short_id(self):
        if self.sub_number >= 0:
            return "%s/%d/%d" % (str(self.plsess), self.number,
                                 self.sub_number)
        else:
            return "%s/%d" % (str(self.plsess), self.number)

    def get_preferred_view_url(self):
        try:
            # By default link to the document page that usually
            # gives a nicer context
            doc = self.docs.all()[0]
            return doc.get_absolute_url()
        except IndexError:
            return self.get_absolute_url()

    def get_absolute_url(self):
        args = {'plsess': self.plsess.url_name,
                'item_nr': self.number}
        if self.sub_number is not None:
            args['subitem_nr'] = self.sub_number
        return reverse('parliament.views.show_item', kwargs=args)

    def get_processing_stage_str(self):
        stages = DocumentProcessingStage.STAGE_CHOICES
        for st in stages:
            if st[0] == self.processing_stage:
                break
        return unicode(st[1])

    def get_type_description(self):
        parts = [
            self.get_type_display(),
            self.sub_description,
            self.get_processing_stage_str() if self.processing_stage else ''
        ]
        parts = filter(None, parts)
        return ", ".join(parts)

    def __unicode__(self):
        return "%s %s: %s" % (self.get_short_id(), self.type, self.description)

class PlenarySessionItemDocument(models.Model):
    item = models.ForeignKey(PlenarySessionItem, db_index=True)
    doc = models.ForeignKey(Document, db_index=True)
    order = models.PositiveIntegerField()

    class Meta:
        app_label = 'parliament'
        ordering = ('order',)
        unique_together = (('item', 'doc'),)

class Statement(models.Model):
    TYPES = (('normal', 'Statement'),
             ('speaker', 'Speaker statement'),)

    item = models.ForeignKey(PlenarySessionItem, db_index=True)
    index = models.PositiveIntegerField(db_index=True)
    member = models.ForeignKey('Member', db_index=True, null=True)
    speaker_name = models.CharField(max_length=40, null=True, blank=True)
    speaker_role = models.CharField(max_length=40, null=True, blank=True)
    # Currently used to differentiate between the speakers and plain MPs
    type = models.CharField(max_length=15, choices=TYPES)

    text = models.TextField()

    class Meta:
        ordering = ('item', 'index')
        app_label = 'parliament'
        unique_together = (('item', 'index'),)

    def get_html_text(self):
        """Text of statement with linefeeds doubled. For use with django |linebreaks"""
        return mark_safe(linebreaks(self.text.replace('\n', '\n\n')))

    def __unicode__(self):
        return "%s/%d (%s)" % (self.item.get_short_id(), self.index, unicode(self.member))

    def get_short_id(self):
        return "%s/%d"%(self.item.get_short_id(), self.index)
    
    def get_indocument_url(self):
        # A hack as the item itself doesn't have a proper
        # page in the system
        return self.item.get_preferred_view_url() + "#statement-" + self.get_short_id()
class PlenaryVoteManager(models.Manager):
    def between(self, begin=None, end=None):
        query = Q()
        if begin:
            query &= Q(plenary_session__date__gte=begin)
        if end:
            query &= Q(plenary_session__date__lte=end)
        return self.filter(query)
    def by_name(self, name):
        f = name.split('/')
        nr = int(f[0])
        pls_name = '/'.join(f[1:])
        return self.get(Q(plenary_session__name=pls_name) & Q(number=nr))

class PlenaryVote(UpdatableModel):
    plsess = models.ForeignKey(PlenarySession, db_index=True)
    plsess_item = models.ForeignKey(PlenarySessionItem, db_index=True, null=True, blank=True, related_name='plenary_votes')
    number = models.IntegerField()
    time = models.DateTimeField()
    subject = models.TextField()
    setting = models.CharField(max_length=200)
    info_link = models.URLField(blank=True, null=True)
    vote_counts = models.CommaSeparatedIntegerField(max_length=20, blank=True,
                                                    null=True)
    docs = models.ManyToManyField(Document, through='PlenaryVoteDocument')
    keywords = models.ManyToManyField(Keyword)

    objects = PlenaryVoteManager()

    def count_votes(self):
        if self.vote_counts:
            return
        vcnt = []
        for v in Vote.VOTE_CHOICES:
            c = Vote.objects.filter(session=self, vote=v[0]).count()
            vcnt.append(str(c))
        self.vote_counts = ','.join(vcnt)

    def get_vote_counts(self):
        if not self.vote_counts:
            self.count_votes()
        vcnt = self.vote_counts.split(',')
        vdict = {}
        for i in range(len(Vote.VOTE_CHOICES)):
            v = Vote.VOTE_CHOICES[i]
            vdict[v[0]] = int(vcnt[i])
        return vdict

    def save(self, *args, **kwargs):
#        query = Q(begin__lte=self.plenary_session.date)
#        query &= Q(end__isnull=True) | Q(end__gte=self.plenary_session.date)
#        MemberStats.objects.filter(query).delete()
        super(PlenaryVote, self).save(args, kwargs)

    def get_short_summary(self):
        lines = []
        for line in self.info.split('\n'):
            if not line:
                continue
            if line[-1] != '.':
                line += '.'
            lines.append(line)
        lines.append(self.subject)
        return ' '.join(lines)

    @models.permalink
    def get_absolute_url(self):
        args = {'plsess': self.plenary_session.url_name, 'sess': self.number}
        return ('votes.views.show_session', (), args)

    def get_json(self):
        arg = {'id': str(self), 'number': self.number, 'time': str(self.time)}
        arg['subject'] = self.subject
        arg['info'] = self.info
        if self.info_link:
            arg['uri'] = self.info_link
        vc = self.get_vote_counts()
        del vc['S']
        arg['vote_counts'] = vc
        votes = self.vote_set.all().select_related('member')
        arg['votes'] = [v.get_json() for v in votes]
        kw_list = self.sessionkeyword_set.all().select_related('keyword')
        arg['keywords'] = [k.keyword.name for k in kw_list]
        return arg

    def __unicode__(self):
        return str(self.number) + '/' + self.plsess.name

    class Meta:
        ordering = ('plsess__date', 'number')
        app_label = 'parliament'

class PlenaryVoteDocument(models.Model):
    session = models.ForeignKey(PlenaryVote)
    doc = models.ForeignKey(Document)
    order = models.PositiveIntegerField()

    class Meta:
        app_label = 'parliament'


class VoteManager(models.Manager):
    def get_count(self, vote=None, session=None, member=None):
        query = Q()
        if type(vote) is list:
            for v in vote:
                query |= Q(vote=v)
        elif vote is not None:
            query |= Q(vote=vote)
        if member is not None:
            query &= Q(member=member.name)
        if session is not None:
            query &= Q(session=session.name)

        return Vote.objects.filter(query).count()
    def in_district(self, district, date_begin, date_end):
        qs = Member.objects.in_district(district, date_begin, date_end)
        qs = qs.values_list('id', flat=True).distinct()
        return Vote.objects.filter(member__in=qs)

class Vote(models.Model):
    VOTE_CHOICES = [
        ('Y', u'Yes'),
        ('N', u'No'),
        ('A', u'Absent'),
        ('E', u'Empty'),
        ('S', u'Speaker')
    ]
    session = models.ForeignKey(PlenaryVote)
    vote = models.CharField(max_length=1, choices=VOTE_CHOICES, db_index=True)
    member = models.ForeignKey('Member', db_index=True)
    party = models.CharField(max_length=10)

    objects = VoteManager()

    def get_json(self):
        return {'member': str(self.member), 'party': self.party,
                'vote': self.vote}

    def __unicode__(self):
        return unicode(self.session) + u' / ' + unicode(self.member.name)

    class Meta:
        app_label = 'parliament'
