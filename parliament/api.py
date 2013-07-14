from django.db import models
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource
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
        n_days = int(bundle.request.GET.get('activity_days', 30))
        activity_start = datetime.datetime.now() - datetime.timedelta(days=n_days)
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

        stats = bundle.request.GET.get('stats', '')
        if stats.lower() in ('1', 'true'):
            bundle.data['stats'] = bundle.obj.get_latest_stats()
            bundle.data['stats']['recent_activity'] = bundle.obj.get_activity_score(activity_start)

        return bundle
    class Meta:
        queryset = Member.objects.select_related('party')

class MemberActivityResource(KamuResource):
    member = fields.ForeignKey('parliament.api.MemberResource', 'member')

    def get_extra_info(self, item):
        d = {}
        if item.type == 'FB':
            d['icon'] = 'facebook'
            o = item.socialupdateactivity.update
            d['text'] = o.text
        elif item.type == 'TW':
            d['icon'] = 'twitter'
            o = item.socialupdateactivity.update
            d['text'] = o.text
        elif item.type == 'ST':
            d['icon'] = 'comment-alt'
            o = item.statementactivity.statement
            d['text'] = o.text
        elif item.type == 'IN':
            d['icon'] = 'lightbulb'
            o = item.initiativeactivity.doc
            d['text'] = o.summary
        elif item.type == 'SI':
            d['icon'] = 'pencil'
            o = item.signatureactivity.signature.doc
            d['text'] = o.summary
        elif item.type == 'WQ':
            d['icon'] = 'question'
            o = item.initiativeactivity.doc
            d['text'] = o.summary
        else:
            return None
        return d

    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data['member_name'] = obj.member.name
        if obj.member.party:
            bundle.data['party_name'] = party_dict[obj.member.party.id].name
        d = self.get_extra_info(obj)
        if d:
            bundle.data.update(d)
        return bundle

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

all_resources = [TermResource, PartyResource, MemberResource, PlenarySessionResource,
                 PlenaryVoteResource, VoteResource, FundingSourceResource, FundingResource,
                 SeatResource, MemberSeatResource, DocumentResource, MemberActivityResource]
