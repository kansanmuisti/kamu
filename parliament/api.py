from django.db import models
from tastypie.resources import ModelResource
from tastypie.exceptions import BadRequest
from tastypie import fields
from parliament.models import *
from sorl.thumbnail import get_thumbnail

term_list = list(Term.objects.visible())

class TermResource(ModelResource):
    class Meta:
        queryset = Term.objects.all()

class PartyResource(ModelResource):
    class Meta:
        queryset = Party.objects.all()

class MemberResource(ModelResource):
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
        return bundle
    class Meta:
        queryset = Member.objects.all()

class PlenarySessionResource(ModelResource):
    plenary_votes = fields.ToManyField('parliament.api.PlenaryVoteResource', 'plenary_vote_set')
    class Meta:
        queryset = PlenarySession.objects.all()
        resource_name = 'plenary_session'

class PlenaryVoteResource(ModelResource):
    votes = fields.ToManyField('parliament.api.VoteResource', 'vote_set', full=True)
    class Meta:
        queryset = PlenaryVote.objects.all()
        resource_name = 'plenary_vote'

class VoteResource(ModelResource):
    plenary_vote = fields.ForeignKey(PlenaryVoteResource, 'plenary_vote')
    member = fields.ForeignKey(MemberResource, 'member')
    class Meta:
        queryset = Vote.objects.all()

class FundingSourceResource(ModelResource):
    class Meta:
        queryset = FundingSource.objects.all()

class FundingResource(ModelResource):
    member = fields.ForeignKey(MemberResource, 'member')
    source = fields.ForeignKey(FundingSourceResource, 'source', null=True, full=True)
    class Meta:
        queryset = Funding.objects.all()

class SeatResource(ModelResource):
    class Meta:
        queryset = Seat.objects.all()

class MemberSeatResource(ModelResource):
    seat = fields.ForeignKey(SeatResource, 'seat', full=True)
    member = fields.ForeignKey(MemberResource, 'member')
    class Meta:
        queryset = MemberSeat.objects.all()

class DocumentResource(ModelResource):
    class Meta:
        queryset = Document.objects.all()

all_resources = [TermResource, PartyResource, MemberResource, PlenarySessionResource,
                 PlenaryVoteResource, VoteResource, FundingSourceResource, FundingResource,
                 SeatResource, MemberSeatResource, DocumentResource]
