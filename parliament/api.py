from django.db import models
from django.http import Http404
from django.conf.urls.defaults import *
from django.core.exceptions import *

from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource, Resource
from tastypie.exceptions import BadRequest
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields
from parliament.models import *
from sorl.thumbnail import get_thumbnail
import datetime


# Save these for caching purposes
term_list = list(Term.objects.visible())
party_list = [(p.id, p) for p in Party.objects.all()]
party_dict = {id: p for id, p in party_list}

class KamuResource(ModelResource):
    def __init__(self, api_name=None):
        super(KamuResource, self).__init__(api_name)
        self._meta.cache = SimpleCache(timeout=3600)

class TermResource(KamuResource):
    class Meta:
        queryset = Term.objects.all()

class PartyResource(KamuResource):
    class Meta:
        queryset = Party.objects.all()

class MemberResource(KamuResource):
    party = fields.ForeignKey('parliament.api.PartyResource', 'party', full=True)

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
        tn_dim = bundle.request.GET.get('thumbnail_dim', None)
        if tn_dim:
            arr = tn_dim.strip().split('x')
            if len(arr) == 2:
                # Make sure they are numbers.
                try:
                    num = [int(x) for x in arr]
                except ValueError:
                    arr = []
            if len(arr) != 2:
                raise BadRequest("Dimensions not in proper format (e.g. 64x96)")
            tn_dim = 'x'.join(arr)
            bundle.data['photo_thumbnail'] = get_thumbnail(bundle.obj.photo, tn_dim).url

        bundle.data['district_name'] = bundle.obj.get_latest_district().name

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
        documents = Document.objects.all()
        if start_date:
            documents = documents.filter(date__gte=start_date)
        
        keywords = Keyword.objects.filter(document__in=documents)
        activity = keywords.annotate(activity=models.Count('id'))
        activity = activity.extra(order_by=['-activity'])
        if limit:
            activity = activity[:limit]

        act_list = [FakeModel(topic=a.name, activity=a.activity) for a in activity]
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
