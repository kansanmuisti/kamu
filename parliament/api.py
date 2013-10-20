from django.db import models
from django.http import Http404
from django.conf.urls.defaults import *
from django.core.exceptions import *
from django.shortcuts import redirect

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

class KamuResource(ModelResource):
    def __init__(self, api_name=None):
        super(KamuResource, self).__init__(api_name)
        self._meta.cache = SimpleCache(timeout=3600)

class TermResource(KamuResource):
    class Meta:
        queryset = Term.objects.all()

class PartyResource(KamuResource):
    SUPPORTED_LOGO_WIDTHS = (32, 48, 64)

    def get_logo(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        try:
            party = Party.objects.get(name=kwargs.get('name'))
        except Party.DoesNotExist:
            return http.HttpNotFound()
        dim = request.GET.get('dim', None)
        if not dim or not re.match(r'[\d]+x[\d]+$', dim):
            raise BadRequest("You must supply the 'dim' parameter for the image dimensions (e.g. 64x64")
        width, height = [int(x) for x in dim.split('x')]
        if width != height:
            raise BadRequest("Only square dimensions (x=y) supported")
        if not width in self.SUPPORTED_LOGO_WIDTHS:
            raise BadRequest("Supported thumbnail widths: %s" % ', '.join([str(x) for x in self.SUPPORTED_LOGO_WIDTHS]))
        fmt = 'PNG' if str(party.logo).endswith('.png') else 'JPEG'
        tn_url = get_thumbnail(party.logo, '%dx%d' % (width, height), format=fmt).url
        return redirect(tn_url)

    def prepend_urls(self):
        url_base = r"^(?P<resource_name>%s)/(?P<name>[\w\d_.-]+)/" % self._meta.resource_name
        return [
            url(url_base + '$', self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(url_base + 'logo/$', self.wrap_view('get_logo'), name="api_get_logo"),
        ]

    class Meta:
        queryset = Party.objects.all()
        detail_uri_name = 'name'

class Committee(KamuResource):
    class Meta:
        queryset = Committee.objects.all()

class CommitteeAssociation(KamuResource):
    class Meta:
        queryset = CommitteeAssociation.objects.all()

class MemberResource(KamuResource):
    party = fields.ForeignKey('parliament.api.PartyResource', 'party')

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

        n_days = int(bundle.request.GET.get('activity_days', 30))
        activity_start = datetime.datetime.now() - datetime.timedelta(days=n_days)
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

class MemberActivityResource(KamuResource):
    member = fields.ForeignKey('parliament.api.MemberResource', 'member')

    def get_extra_info(self, item):
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
        elif acttype == 'IN':
            o = item.initiativeactivity.doc
            target['text'] = o.summary
            target['subject'] = o.subject
            target['name'] = o.name
        elif acttype == 'SI':
            o = item.signatureactivity.signature.doc
            target['text'] = o.summary
            target['subject'] = o.subject
            target['name'] = o.name
            target['type'] = o.type
        elif acttype == 'WQ':
            o = item.initiativeactivity.doc
            target['text'] = o.summary
            target['subject'] = o.subject
            target['name'] = o.name
        else:
            raise Exception("Invalid type %s" % acttype)
        d['target'] = target
        return d

    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data['member_name'] = obj.member.name
        bundle.data['type'] = obj.type.pk
        if obj.member.party:
            bundle.data['party_name'] = party_dict[obj.member.party.id].name
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
        queryset = MemberActivity.objects.all().order_by('-time').select_related('member')
        resource_name = 'member_activity'
        filtering = {
            'type': ('exact', 'in'),
            'time': ALL,
            'member': ALL_WITH_RELATIONS
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
    class Meta:
        queryset = Document.objects.all()

class FakeModel(object):
    def __init__(self, **initial):
        self.__dict__['_data'] = {}
        self.__dict__['_data'].update(initial)

    def __getattr__(self, name):
        return self.__dict__['_data'].get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data

class TopicActivityResource(Resource):
    topic = fields.CharField(attribute='topic')
    activity = fields.FloatField(attribute='activity')

    class Meta:
        resource_name = 'topic_activity'
        object_class = FakeModel

    def get_object_list(self, start_date=None, limit=None):
        activities = KeywordActivity.objects

        if start_date:
            activities = activities.filter(activity__time__gte=start_date)
    
        activity = activities.values('keyword__name').annotate(
            activity=models.Sum('activity__type__weight'),
            last_date=models.Max('activity__time'),
        )

        activity = activity.extra(order_by=['-activity'])
        if limit:
            activity = activity[:limit]

        act_list = [
            FakeModel(
                topic=a['keyword__name'],
                activity=a['activity'],
                last_date=a['last_date'])
            for a in activity]
        return act_list

    
    def obj_get_list(self, bundle, **kwargs):
        since = bundle.request.GET.get('since', None)
        if since:
            start_date = datetime.datetime.strptime(since, '%Y-%m-%d')
        else:
            start_date = None

        return self.get_object_list(start_date=start_date)

all_resources = [TermResource, PartyResource, MemberResource, PlenarySessionResource,
                 PlenaryVoteResource, VoteResource, FundingSourceResource, FundingResource,
                 SeatResource, MemberSeatResource, DocumentResource, MemberActivityResource, TopicActivityResource]
