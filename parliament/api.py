from django.db import models
from tastypie.resources import ModelResource
from tastypie import fields
from parliament.models import *

class TermResource(ModelResource):
    class Meta:
        queryset = Term.objects.all()

class PartyResource(ModelResource):
    class Meta:
        queryset = Party.objects.all()

class MemberResource(ModelResource):
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
