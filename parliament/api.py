from django.db import models
from django.http import Http404
from django.conf.urls.defaults import *
from django.core.exceptions import *
from django.shortcuts import redirect
from dateutil.relativedelta import relativedelta

from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource, Resource
from tastypie.exceptions import BadRequest
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields, http
from parliament.models import *
from sorl.thumbnail import get_thumbnail
import datetime
import re


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
            num = [int(x) for x in arr]
        except ValueError:
            arr = []
    if len(arr) != 2:
        raise BadRequest("Thumbnail dimensions not in proper format (e.g. 64x96)")
    tn_dim = 'x'.join(arr)
    bundle.data[field_name] = get_thumbnail(image, tn_dim).url

def parse_date_from_opts(options, field_name):
    val = options.get(field_name, None)
    if not val:
        return None
    val = val.lower()
    if val == 'month':
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
    type=fields.CharField(attribute='type')
    score=fields.FloatField(attribute='score')
    time=fields.DateTimeField(attribute="activity_date")

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
                                                resolution=resolution)
        bundle=[]
        for score in score_list:
            score_obj = DictModel(score)
            bundle.append(score_obj)

        return bundle

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        return self.parent_uri

    class Meta:
        include_resource_uri = False
        resource_name = 'activity_scores'

class PartyResource(KamuResource):
    SUPPORTED_LOGO_DIMS = ((32, 32), (48, 48), (64, 64), (128,128))

    def get_logo(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        try:
            party = Party.objects.get(name=kwargs.get('name'))
        except Party.DoesNotExist:
            return http.HttpNotFound()
        return api_get_thumbnail(request, party.logo, self.SUPPORTED_LOGO_DIMS)

    def prepend_urls(self):
        url_base = r"^(?P<resource_name>%s)/(?P<name>[\w\d_.-]+)/" % self._meta.resource_name
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
        if 'name' in kwargs:
            party_name = kwargs.get('name')
            try:
                party = Party.objects.get(name=party_name)
            except Party.DoesNotExist:
                raise Http404("Party '%s' does not exist" % party_name)
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
        bundle.data['governing_party'] = party.is_currently_governing()
        # This tests for whether the member has a ministryassociation that has not ended. (Begin condition
        # is due to to the null testing on right side of left join)
        bundle.data['minister_count'] = party.member_set.filter(ministryassociation__isnull=False,ministryassociation__end__isnull=True).count()
        return bundle

    class Meta:
        queryset = Party.objects.all()
        detail_uri_name = 'name'

class CommitteeResource(KamuResource):
    class Meta:
        queryset = Committee.objects.all()

class CommitteeAssociationResource(KamuResource):
    class Meta:
        queryset = CommitteeAssociation.objects.all()

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

    def dehydrate(self, bundle):
        process_api_thumbnail(bundle, bundle.obj.photo, 'photo_thumbnail')
        bundle.data['district_name'] = bundle.obj.get_latest_district().name

        posts = bundle.obj.get_posts()
        d = {'ministry': [{'begin': x.begin, 'end': x.end, 'label': x.label, 'role': x.role} for x in posts['ministry']]}
        d['committee'] = [{'begin': x.begin, 'end': x.end, 'committee': x.committee.name, 'role': x.role} for x in posts['committee']]
        bundle.data['posts'] = d

        bundle.data['terms'] = [term.name for term in bundle.obj.get_terms()]
        bundle.data['age'] = bundle.obj.get_age()

        opts = {'since': bundle.request.GET.get('activity_days', 'term')}
        activity_start = parse_date_from_opts(opts, 'since')
        stats = bundle.request.GET.get('stats', '')
        if stats.lower() in ('1', 'true'):
            bundle.data['stats'] = bundle.obj.get_latest_stats()
            bundle.data['stats']['recent_activity'] = bundle.obj.get_activity_score(activity_start)

        activity_counts = bundle.request.GET.get('activity_counts', '')
        if activity_counts.lower() in ('1', 'true'):
            bundle.data['activity_counts'] = bundle.obj.get_activity_counts()

        return bundle

    class Meta:
        queryset = Member.objects.select_related('party')

class MemberActivityTypeResource(KamuResource):
    class Meta:
        resource_name = 'member_activity_type'
        queryset = MemberActivityType.objects
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
        if acttype == 'FB':
            o = item.socialupdateactivity.update
            target['text'] = o.text
        elif acttype == 'TW':
            o = item.socialupdateactivity.update
            target['text'] = o.text
        elif acttype == 'ST':
            o = item.statementactivity.statement
            target['text'] = o.text
        elif acttype in ('IN', 'WQ', 'GB', 'SI'):
            if acttype == 'SI':
                o = item.signatureactivity.signature.doc
            else:
                o = item.initiativeactivity.doc
            target['text'] = o.summary
            target['subject'] = o.subject
            target['name'] = o.name
            target['type'] = o.type
            target['keywords'] = get_keywords(o)
            target['url'] = o.get_absolute_url()
        else:
            raise Exception("Invalid type %s" % acttype)
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

class PlenarySessionResource(KamuResource):
    plenary_votes = fields.ToManyField('parliament.api.PlenaryVoteResource', 'plenary_vote_set')
    class Meta:
        queryset = PlenarySession.objects.all()
        resource_name = 'plenary_session'

class PlenaryVoteResource(KamuResource):
    votes = fields.ToManyField('parliament.api.VoteResource', 'vote_set', full=True)
    class Meta:
        queryset = PlenaryVote.objects.all()
        resource_name = 'plenary_vote'

class VoteResource(KamuResource):
    plenary_vote = fields.ForeignKey(PlenaryVoteResource, 'plenary_vote')
    member = fields.ForeignKey(MemberResource, 'member')
    class Meta:
        queryset = Vote.objects.all()

class FundingSourceResource(KamuResource):
    class Meta:
        queryset = FundingSource.objects.all()

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

    def dehydrate(self, bundle):
        obj = bundle.obj
        if getattr(obj, 'activity_score', None) is not None:
            bundle.data['activity_score'] = obj.activity_score
        if getattr(obj, 'last_date', None) is not None:
            bundle.data['last_date'] = obj.last_date
        bundle.data['slug'] = obj.get_slug()

        if bundle.request.GET.get('related', '').lower() in ('true', '1'):
            qs = Keyword.objects.filter(document__in=bundle.obj.document_set.all()).distinct()
            qs = qs.annotate(count=models.Count('document')).filter(document__in=bundle.obj.document_set.all())
            qs = qs.order_by('-count')[0:20]
            related_kws = [{'id': kw.id, 'name': kw.name, 'slug': kw.get_slug(), 'count': kw.count} for kw in qs if kw.id != bundle.obj.id]
            bundle.data['related'] = related_kws

        if bundle.request.GET.get('most_active', '').lower() in ('true', '1'):
            mp_list = Member.objects.filter(memberactivity__keywordactivity__keyword=bundle.obj).annotate(score=models.Sum('memberactivity__type__weight')).order_by('-score')
            party_list = Party.objects.filter(member__memberactivity__keywordactivity__keyword=bundle.obj).annotate(score=models.Sum('member__memberactivity__type__weight')).order_by('-score')
            d = {}
            d['members'] = [{'id': mp.id, 'name': mp.get_print_name(), 'url_name': mp.url_name, 'score': mp.score} for mp in mp_list[0:10]]
            #FIXME: Party data should be averaged to per-MP values
            d['parties'] = [{'id': party.id, 'name': party.name, 'full_name': party.full_name, 'score': party.score} for party in party_list]
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

all_resources = [TermResource, PartyResource, MemberResource, PlenarySessionResource,
                 PlenaryVoteResource, VoteResource, FundingSourceResource, FundingResource,
                 SeatResource, MemberSeatResource, DocumentResource, MemberActivityResource,
                 KeywordResource, CommitteeResource, KeywordActivityResource, KeywordResource,
                 ActivityScoresResource]
