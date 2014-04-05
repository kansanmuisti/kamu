from django.db import models
from django.http import Http404
from django.conf.urls import url
from django.conf import settings
from django.core.exceptions import *
from django.db.models import Sum
from django.shortcuts import redirect
from dateutil.relativedelta import relativedelta

from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource, Resource
from tastypie.exceptions import BadRequest
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields, http
from sorl.thumbnail import get_thumbnail
import datetime
import re

from parliament.models import *
from social.api import UpdateResource

# Save these for caching purposes
term_list = list(Term.objects.visible())
party_list = [(p.id, p) for p in Party.objects.all()]
party_dict = {id: p for id, p in party_list}

def process_api_thumbnail(bundle, image, field_name):
    tn_dim = bundle.request.GET.get('thumbnail_dim', None)
    if not tn_dim:
        return
    arr = tn_dim.strip().split('x')
    if len(arr) == 2:
        # Make sure they are numbers.
        try:
            [int(x) for x in arr]
        except ValueError:
            arr = []
    if len(arr) != 2:
        raise BadRequest("Thumbnail dimensions not in proper format (e.g. 64x96)")
    tn_dim = 'x'.join(arr)
    bundle.data[field_name] = get_thumbnail(image, tn_dim).url

def parse_date_from_opts(options, field_name, default=None):
    val = options.get(field_name, None)
    if not val:
        if not default:
            return None
        val = default

    val = val.lower()
    if val == 'month':
        return datetime.date.today() - relativedelta(months=1)
    elif val == '2months':
        return datetime.date.today() - relativedelta(months=2)
    elif val == 'term':
        return Term.objects.latest().begin
    try:
        date_val = datetime.datetime.strptime(val, '%Y-%m-%d')
    except ValueError:
        raise BadRequest("'%s' must be in ISO date format (yyyy-mm-dd)" % field_name)

    return date_val

class KamuResource(ModelResource):
    def __init__(self, api_name=None):
        super(KamuResource, self).__init__(api_name)
        self._meta.cache = SimpleCache(timeout=3600)
        self._meta.list_allowed_methods = ['get']
        self._meta.detail_allowed_methods = ['get']

class TermResource(KamuResource):
    class Meta:
        queryset = Term.objects.all()

def api_get_thumbnail(request, image, supported_dims):
    dim = request.GET.get('dim', None)
    if not dim or not re.match(r'[\d]+x[\d]+$', dim):
        raise BadRequest("You must supply the 'dim' parameter for the image dimensions (e.g. 64x64")
    width, height = [int(x) for x in dim.split('x')]
    if not (width, height) in supported_dims:
        dims = ', '.join([('%dx%d' % (x[0], x[1])) for x in supported_dims])
        raise BadRequest("Supported thumbnail dimensions: %s" % dims)
    fmt = 'PNG' if str(image).endswith('.png') else 'JPEG'
    tn_url = get_thumbnail(image, '%dx%d' % (width, height), format=fmt).url
    return redirect(tn_url)

class DictModel(object):
    def __init__(self, base_dict):
        self.__base_dict = base_dict

    def __getattr__(self, key):
        value = self.__base_dict[key]
        if type(value) == type({}):
            return DictModel(value)

        return value

class ActivityScoresResource(Resource):
    type = fields.CharField(attribute='type')
    score = fields.FloatField(attribute='score')
    time = fields.DateTimeField(attribute='activity_date')

    def get_list(self, request, **kwargs):
        self.parent_object = kwargs.get('parent_object')
        if self.parent_object is None:
            raise BadRequest('Missing parent object. Trying to get this as a non-nested resource?')

        self.parent_uri = kwargs.get('parent_uri')
        if self.parent_uri is None:
            raise BadRequest('Missing parent uri.')

        return super(ActivityScoresResource, self).get_list(request, **kwargs)

    def obj_get_list(self, bundle, **kwargs):
        resolution=bundle.request.GET.get('resolution', '').lower()
        if resolution == '':
            resolution = None

        since = parse_date_from_opts(bundle.request.GET, 'since')
        until = parse_date_from_opts(bundle.request.GET, 'until')

        obj = self.parent_object
        score_list = obj.get_activity_score_set(since=since, until=until,
                                                resolution=resolution,
                                                **kwargs)
        bundle = []
        for score in score_list:
            score_obj = DictModel(score)
            bundle.append(score_obj)

        return bundle

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        return self.parent_uri

    class Meta:
        include_resource_uri = False
        resource_name = 'activity_scores'

class ParliamentResource(Resource):
    class ParliamentHelper(object):
        def get_activity_score_set(self, **kwargs):
            scores = MemberActivity.objects.get_score_set(**kwargs)
            if 'calc_average' in kwargs:
                for s in scores:
                    s['score'] /= settings.NUMBER_OF_MPS

            return scores

    def get_parliament_activity_scores(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)

        obj = self.ParliamentHelper()
        scores_resource = ActivityScoresResource()
        uri_base = self._build_reverse_url('api_get_parliament_activity_scores',
                                       kwargs=self.resource_uri_kwargs(obj))

        if request.GET.get('calculate_average', '').lower() in ['true', '1']:
            kwargs['calc_average'] = 1

        return scores_resource.get_list(request, parent_object=obj,
                                        parent_uri=uri_base, **kwargs)

    def prepend_urls(self):
        url_base = r"^(?P<resource_name>%s)/" % self._meta.resource_name
        return [
            url(url_base + 'activity_scores/$',
                self.wrap_view('get_parliament_activity_scores'),
                name="api_get_parliament_activity_scores"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj=None):
        return {}

    class Meta:
        dummy = 1

class PartyResource(KamuResource):
    SUPPORTED_LOGO_DIMS = ((32, 32), (48, 48), (64, 64), (128,128))

    def get_logo(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        try:
            party = Party.objects.get(abbreviation=kwargs.get('abbreviation'))
        except Party.DoesNotExist:
            return http.HttpNotFound()
        return api_get_thumbnail(request, party.logo, self.SUPPORTED_LOGO_DIMS)

    def prepend_urls(self):
        url_base = r"^(?P<resource_name>%s)/(?P<abbreviation>[\w\d_.-]+)/" % self._meta.resource_name
        return [
            url(url_base + '$', self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(url_base + 'logo/$', self.wrap_view('get_logo'), name="api_get_logo"),
            url(url_base + 'activity_scores/$',
                self.wrap_view('get_party_activity_scores'),
                name="api_get_party_activity_scores"),
        ]

    def get_party(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        if 'abbreviation' in kwargs:
            party_abbreviation = kwargs.get('abbreviation')
            try:
                party = Party.objects.get(abbreviation=party_abbreviation)
            except Party.DoesNotExist:
                raise Http404("Party '%s' does not exist" % party_abbreviation)
        else:
            party_id = kwargs.get('pk')
            try:
                party = Party.objects.get(pk=party_id)
            except Party.DoesNotExist:
                raise Http404("Party ID '%s' does not exist" % party_id)

        return party

    def get_party_activity_scores(self, request, **kwargs):
        obj = self.get_party(request, **kwargs)
        scores_resource = ActivityScoresResource()
        uri_base = self._build_reverse_url('api_get_party_activity_scores',
                                       kwargs=self.resource_uri_kwargs(obj))

        return scores_resource.get_list(request, parent_object=obj,
                                        parent_uri=uri_base, **kwargs)
    def dehydrate(self, bundle):
        party = bundle.obj
        bundle.data['logo_128x128'] = get_thumbnail(party.logo, '128x128', format='PNG').url
        bundle.data['member_count'] = party.member_set.current().count()
        bundle.data['governing_now'] = party.is_governing()

        gps = party.governingparty_set.order_by('begin')
        d = [{'begin': gp.begin, 'end': gp.end} for gp in gps]
        bundle.data['governing_terms'] = d

        # This tests for whether the member has a ministryassociation that has not ended. (Begin condition
        # is due to to the null testing on right side of left join)
        bundle.data['minister_count'] = party.member_set.filter(ministryassociation__isnull=False,ministryassociation__end__isnull=True).count()

        opts = {'since': bundle.request.GET.get('activity_since', 'term')}
        activity_start = parse_date_from_opts(opts, 'since')

        recent_keywords = bundle.request.GET.get('recent_keywords', '')
        if recent_keywords.lower() in ('1', 'true'):
            # Add keywords with most recent activity
            kwa_list = KeywordActivity.objects.filter(activity__member__party=bundle.obj).filter(activity__time__gte=activity_start)
            qs = Keyword.objects.filter(keywordactivity__in=kwa_list)
            qs = qs.annotate(score=Sum('keywordactivity__activity__type__weight')).order_by('-score')
            kw_list = qs[0:5]
            bundle.data['recent_keywords'] = [
                {'id': kw.id, 'score': kw.score, 'name': kw.name, 'slug': kw.get_slug()} for kw in kw_list
            ]

        stats = bundle.request.GET.get('stats', '')
        if stats.lower() in ('1', 'true'):
            bundle.data['stats'] = {}
            score = bundle.obj.get_activity_score(begin=activity_start)
            bundle.data['stats']['recent_activity'] = score
            # Could be calculated only once per request, but tastypie
            # probably makes this difficult and we are very slow already
            days = (datetime.date.today() - activity_start).days
            bundle.data['stats']['activity_days_included'] = days

        return bundle

    class Meta:
        queryset = Party.objects.all()
        detail_uri_name = 'abbreviation'

class CommitteeResource(KamuResource):
    class Meta:
        queryset = Committee.objects.all()

class CommitteeAssociationResource(KamuResource):
    class Meta:
        queryset = CommitteeAssociation.objects.all()


# Arguments:
#   - current (bool)
#   - stats (bool)
#   - include_activity (bool)
#   - activity_since (time ago)
#   - activity_counts (bool)

class MemberResource(KamuResource):
    SUPPORTED_PORTRAIT_DIMS = ((48, 72), (64, 96), (106, 159), (128, 192))

    party = fields.ForeignKey('parliament.api.PartyResource', 'party')

    def prepend_urls(self):
        url_base = r"^(?P<resource_name>%s)/(?P<pk>\d+)/" % self._meta.resource_name
        return [
            url(url_base + 'portrait/$', self.wrap_view('get_portrait'), name="api_get_portrait"),
            url(url_base + 'activity_scores/$',
                self.wrap_view('get_member_activity_scores'),
                name="api_get_member_activity_scores"),
        ]

    def get_member(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        member_id = kwargs.get('pk')
        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            raise Http404("Member ID '%s' does not exist" % member_id)

        return member

    def get_portrait(self, request, **kwargs):
        member = self.get_member(request, **kwargs)
        return api_get_thumbnail(request, member.photo, self.SUPPORTED_PORTRAIT_DIMS)

    def get_member_activity_scores(self, request, **kwargs):
        obj = self.get_member(request, **kwargs)
        scores_resource = ActivityScoresResource()
        uri_base = self._build_reverse_url('api_get_member_activity_scores',
                                    kwargs=self.resource_uri_kwargs(obj))

        return scores_resource.get_list(request, parent_object=obj,
                                        parent_uri=uri_base, **kwargs)

    def build_filters(self, filters=None):
        orm_filters = super(MemberResource, self).build_filters(filters)
        return orm_filters
    def apply_filters(self, request, applicable_filters):
        qset = super(MemberResource, self).apply_filters(request, applicable_filters)
        if request.GET.get('current', '').lower() in ('1', 'true'):
            current_term = term_list[0]
            qset = qset & Member.objects.active_in_term(current_term)
        return qset

    def apply_sorting(self, obj_list, options=None):
        if 'order_by' in options:
            val = options['order_by']
            if val[0] == '-':
                val = val[1:]
            if val == 'activity_score':
                since = parse_date_from_opts(options, 'activity_since', 'term')
                # NOTE! This must produce same results as Member.get_activity_score
                # for the responses to makes sense.
                obj_list = obj_list.filter(memberactivity__time__gte=since)
                obj_list = obj_list.annotate(activity_score=models.Sum('memberactivity__type__weight'))
                obj_list = obj_list.order_by(options['order_by'])
                return obj_list

        return super(MemberResource, self).apply_sorting(obj_list, options)

    def dehydrate(self, bundle):
        process_api_thumbnail(bundle, bundle.obj.photo, 'photo_thumbnail')
        bundle.data['district_name'] = bundle.obj.get_latest_district().name

        if bundle.request.GET.get('all_posts', '').lower() in ('true', '1'):
            current = False
        else:
            current = True
        posts = bundle.obj.get_posts(current)
        d = {'ministry': [{'begin': x.begin, 'end': x.end, 'label': x.label, 'role': x.role} for x in posts['ministry']]}
        d['committee'] = [{'begin': x.begin, 'end': x.end, 'committee': x.committee.name, 'role': x.role} for x in posts['committee']]
        d['speaker'] = [{'begin': x.begin, 'end': x.end, 'role': x.role} for x in posts['speaker']]
        bundle.data['posts'] = d

        bundle.data['terms'] = [term.name for term in bundle.obj.get_terms()]
        bundle.data['age'] = bundle.obj.get_age()

        pa_list = []
        for pa in bundle.obj.partyassociation_set.all().order_by('begin'):
            if pa.party:
                abbr = pa.party.abbreviation
            else:
                abbr = pa.name
            d = {'party': abbr, 'begin': pa.begin, 'end': pa.end}
            pa_list.append(d)
        bundle.data['party_associations'] = pa_list
        opts = {'since': bundle.request.GET.get('activity_since', 'term')}
        activity_since = parse_date_from_opts(opts, 'since')
        stats = bundle.request.GET.get('stats', '')
        if stats.lower() in ('1', 'true'):
            # FIXME: What is "latest!?"
            bundle.data['stats'] = bundle.obj.get_latest_stats()

            # If sorting is used, the activity score is calculated
            # already during sorting. This will be added later on.
            if not hasattr(bundle.obj, 'activity_score'):
                bundle.obj.activity_score = bundle.obj.get_activity_score(activity_since)

        if hasattr(bundle.obj, 'activity_score'):
            bundle.data['activity_score'] = bundle.obj.activity_score

        if 'activity_score' in bundle.data:
            # Could be calculated only once per request, but tastypie
            # probably makes this difficult and we are very slow already
            bundle.data['activity_days_included'] = (datetime.date.today() - activity_since).days

        activity_counts = bundle.request.GET.get('activity_counts', '')
        if activity_counts.lower() in ('1', 'true'):
            resolution = bundle.request.GET.get(
                'activity_counts_resolution', None)
            bundle.data['activity_counts'] = bundle.obj.get_activity_counts(
                since=activity_since, resolution=resolution)

        return bundle

    class Meta:
        queryset = Member.objects.all().exclude(origin_id__startswith='nonmp')
        ordering = ['activity_score']
        filtering = {
            'party': ('exact',),
            'name': ('exact', 'in'),
        }

class PlenarySessionResource(KamuResource):
    plenary_votes = fields.ToManyField('parliament.api.PlenaryVoteResource', 'plenaryvote_set', null=True)
    class Meta:
        queryset = PlenarySession.objects.all()
        resource_name = 'plenary_session'

class PlenarySessionItemResource(KamuResource):
    plenary_session = fields.ForeignKey(PlenarySessionResource, 'plsess')
    documents = fields.ManyToManyField('parliament.api.DocumentResource', 'docs', full=False)
    plenary_votes = fields.OneToManyField('parliament.api.PlenaryVoteResource', 'plenary_votes', full=False, null=True)
    class Meta:
        queryset = PlenarySessionItem.objects.all()
        resource_name = 'plenary_session_item'
        filtering = {
            'plenary_session': ALL_WITH_RELATIONS,
            'processing_stage': ALL,
            'nr_votes': ALL,
            'nr_statements': ALL,
        }
        ordering = ['plenary_session']

class PlenaryVoteResource(KamuResource):
    plenary_session = fields.ForeignKey(PlenarySessionResource, 'plsess')
    session_item = fields.ForeignKey(PlenarySessionItemResource, 'plsess_item')

    def dehydrate_vote_counts(self, bundle):
        return bundle.obj.get_vote_counts()

    class Meta:
        queryset = PlenaryVote.objects.all()
        resource_name = 'plenary_vote'
        filtering = {
            'plenary_session': ALL_WITH_RELATIONS,
            'session_item': ALL_WITH_RELATIONS,
        }

class VoteResource(KamuResource):
    plenary_vote = fields.ForeignKey(PlenaryVoteResource, 'session')
    member = fields.ForeignKey(MemberResource, 'member')
    class Meta:
        queryset = Vote.objects.all()
        filtering = {
          'plenary_vote': ALL_WITH_RELATIONS,
          'member': ALL_WITH_RELATIONS,
          'vote': ['in', 'exact']
        }

class StatementResource(KamuResource):
    member = fields.ForeignKey('parliament.api.MemberResource', 'member', null=True)
    session_item = fields.ForeignKey(PlenarySessionItemResource, 'item')

    class Meta:
        resource_name = 'statement'
        queryset = Statement.objects.all()
        filtering = {
            'member': ['exact', 'in']
        }


class MemberActivityTypeResource(KamuResource):
    class Meta:
        resource_name = 'member_activity_type'
        queryset = MemberActivityType.objects.all()
        filtering = {
            'type': ['exact', 'in']
        }

class MemberActivityResource(KamuResource):
    member = fields.ForeignKey('parliament.api.MemberResource', 'member', null=True)
    type = fields.ForeignKey(MemberActivityTypeResource, 'type')

    def get_extra_info(self, item):
        def get_keywords(doc):
            keywords = [{'id': kw.id, 'name': kw.name, 'slug': kw.get_slug()} for kw in doc.keywords.all()]
            return keywords

        d = {}
        target = {}
        acttype = item.type.pk
        if acttype in ('FB', 'TW'):
            o = item.socialupdateactivity.update
            res_class = UpdateResource
            target['text'] = o.text
            target['url'] = o.get_origin_url()
        elif acttype == 'ST':
            o = item.statementactivity.statement
            res_class = StatementResource
            target['text'] = o.text
            target['url'] = o.get_indocument_url()
        elif acttype in ('IN', 'WQ', 'GB', 'SI'):
            if acttype == 'SI':
                o = item.signatureactivity.signature.doc
            else:
                o = item.initiativeactivity.doc
            res_class = DocumentResource
            target['text'] = o.summary
            target['subject'] = o.subject
            target['name'] = o.name
            target['type'] = o.type
            target['keywords'] = get_keywords(o)
            target['url'] = o.get_absolute_url()
        else:
            raise Exception("Invalid type %s" % acttype)

        res = res_class()
        uri = res.get_resource_uri(o)
        target['resource_uri'] = uri

        d['target'] = target
        return d

    def dehydrate(self, bundle):
        obj = bundle.obj
        if obj.member:
            bundle.data['member_name'] = obj.member.name
            bundle.data['member_slug'] = obj.member.url_name
            if obj.member.party:
                bundle.data['party_name'] = party_dict[obj.member.party.id].name

        bundle.data['type'] = obj.type.pk
        d = self.get_extra_info(obj)
        if d:
            bundle.data.update(d)
        return bundle

    def apply_filters(self, request, applicable_filters):
        qset = super(MemberActivityResource, self).apply_filters(request, applicable_filters)
        kw_name = request.GET.get('keyword', None)
        if kw_name:
            try:
                keyword = Keyword.objects.get(name__iexact=kw_name)
            except Keyword.DoesNotExist:
                raise Http404("Keyword '%s' does not exist" % kw_name)
            qset = qset.filter(keywordactivity__keyword=keyword).distinct()
        return qset

    class Meta:
        queryset = MemberActivity.objects.all().order_by('-time').select_related('member').select_related('type')
        resource_name = 'member_activity'
        filtering = {
            'type': ALL_WITH_RELATIONS,
            'time': ALL,
            'member': ALL_WITH_RELATIONS
        }

class KeywordActivityResource(KamuResource):
    activity = fields.ForeignKey(MemberActivityResource, 'activity', full=True)
    keyword = fields.ForeignKey('parliament.api.KeywordResource', 'keyword')

    class Meta:
        queryset = KeywordActivity.objects.all().order_by('-activity__time')
        resource_name = 'keyword_activity'
        filtering = {
            'keyword': ('exact', 'in'),
            'activity': ALL_WITH_RELATIONS
        }

class FundingSourceResource(KamuResource):
    class Meta:
        queryset = FundingSource.objects.all()
        resource_name = 'funding_source'

class FundingResource(KamuResource):
    member = fields.ForeignKey(MemberResource, 'member')
    source = fields.ForeignKey(FundingSourceResource, 'source', null=True, full=True)
    class Meta:
        queryset = Funding.objects.all()

class SeatResource(KamuResource):
    class Meta:
        queryset = Seat.objects.all()

class MemberSeatResource(KamuResource):
    seat = fields.ForeignKey(SeatResource, 'seat', full=True)
    member = fields.ForeignKey(MemberResource, 'member')
    class Meta:
        queryset = MemberSeat.objects.all()
        resource_name = 'member_seat'

class DocumentResource(KamuResource):
    def dehydrate(self, bundle):
        bundle.data['type_name'] = bundle.obj.get_type_display()
        return bundle

    class Meta:
        queryset = Document.objects.all()

class KeywordResource(KamuResource):
    class Meta:
        filtering = {
            'name': ('exact', 'iexact', 'startswith', 'contains', 'icontains')
        }
        queryset = Keyword.objects.all()
        max_limit = 5000

    def get_keyword(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        keyword_id = kwargs.get('pk')
        try:
            keyword = Keyword.objects.get(pk=keyword_id)
        except Keyword.DoesNotExist:
            raise Http404("Keyword ID '%s' does not exist" % keyword_id)

        return keyword

    def prepend_urls(self):
        url_base = r"^(?P<resource_name>%s)/(?P<pk>\d+)/" % self._meta.resource_name
        return [
            url(url_base + 'activity_scores/$',
                self.wrap_view('get_keyword_activity_scores'),
                name="api_get_keyword_activity_scores"),
        ]

    def get_keyword_activity_scores(self, request, **kwargs):
        obj = self.get_keyword(request, **kwargs)
        scores_resource = ActivityScoresResource()
        uri_base = self._build_reverse_url('api_get_keyword_activity_scores',
                                       kwargs=self.resource_uri_kwargs(obj))

        return scores_resource.get_list(request, parent_object=obj,
                                        parent_uri=uri_base, **kwargs)

    def dehydrate(self, bundle):
        obj = bundle.obj
        if getattr(obj, 'activity_score', None) is not None:
            bundle.data['activity_score'] = obj.activity_score
        if getattr(obj, 'last_date', None) is not None:
            bundle.data['last_date'] = obj.last_date
        bundle.data['slug'] = obj.get_slug()

        latest_term = Term.objects.latest()

        if bundle.request.GET.get('related', '').lower() in ('true', '1'):
            qs = Keyword.objects.filter(document__in=bundle.obj.document_set.all()).distinct()
            qs = qs.annotate(count=models.Count('document')).filter(document__in=bundle.obj.document_set.all())
            qs = qs.order_by('-count')[0:20]
            related_kws = [{'id': kw.id, 'name': kw.name, 'slug': kw.get_slug(), 'count': kw.count} for kw in qs if kw.id != bundle.obj.id]
            bundle.data['related'] = related_kws

        if bundle.request.GET.get('most_active', '').lower() in ('true', '1'):
            mp_list = Member.objects.active_in_term(latest_term).filter(memberactivity__keywordactivity__keyword=bundle.obj)
            mp_list = mp_list.distinct().annotate(score=models.Sum('memberactivity__type__weight')).order_by('-score')
            party_dict = {}
            for p in Party.objects.all():
                p.mp_count = p.member_set.active_in_term(latest_term).count()
                p.score = 0
                party_dict[p.id] = p
            for mp in mp_list:
                party_dict[mp.party_id].score += mp.score
            for p in party_dict.values():
                if p.mp_count:
                    p.score /= p.mp_count
                else:
                    assert p.score == 0

            party_list = party_dict.values()
            party_list = sorted(party_list, key=lambda p: p.score, reverse=True)

            d = {}
            d['members'] = [{'id': mp.id, 'name': mp.get_print_name(), 'url_name': mp.url_name, 'score': mp.score} for mp in mp_list[0:10]]
            #FIXME: Party data should be averaged to per-MP values
            d['parties'] = [{'id': party.id, 'abbreviation': party.abbreviation, 'name': party.name, 'score': party.score, 'mp_count': party.mp_count} for party in party_list]
            bundle.data['most_active'] = d

        return bundle

    def apply_sorting(self, obj_list, options=None):
        obj_list = super(KeywordResource, self).apply_sorting(obj_list, options)
        if options.get('activity', '').lower() in ('true', '1'):
            # Activity filtering and sorting
            since = parse_date_from_opts(options, 'since')
            q = Q()
            if since:
                q &= Q(keywordactivity__activity__time__gte=since)

            until = parse_date_from_opts(options, 'until')
            if until:
                q &= Q(keywordactivity__activity__time__lte=until)
            obj_list = obj_list.filter(q)

            obj_list = obj_list.annotate(activity_score=models.Sum('keywordactivity__activity__type__weight'))
            obj_list = obj_list.filter(activity_score__gt=0).order_by('-activity_score')
        if options.get('last_date', '').lower() in ('true', '1'):
            obj_list = obj_list.annotate(last_date=models.Max('keywordactivity__activity__time'))

        return obj_list

all_resources = [TermResource, ParliamentResource, PartyResource, MemberResource, PlenarySessionResource,
                 PlenaryVoteResource, VoteResource, FundingSourceResource, FundingResource,
                 SeatResource, MemberSeatResource, DocumentResource, MemberActivityResource,
                 KeywordResource, CommitteeResource, KeywordActivityResource,
                 PlenarySessionItemResource, StatementResource]
