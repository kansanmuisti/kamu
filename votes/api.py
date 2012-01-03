from django.conf.urls.defaults import url
from tastypie import fields
from tastypie.resources import ModelResource
from votes.models import *

class PartyResource(ModelResource):
    class Meta:
        queryset = Party.objects.all()
        allowed_methods = ['get']

class MemberResource(ModelResource):
    class Meta:
        queryset = Member.objects.all()
        allowed_methods = ['get']

class PlenarySessionResource(ModelResource):
    sessions = fields.ToManyField('votes.api.SessionResource', 'session_set')
    class Meta:
        queryset = PlenarySession.objects.all()
        resource_name = 'plenary_session'
        allowed_methods = ['get']

class SessionResource(ModelResource):
    votes = fields.ToManyField('votes.api.VoteResource', 'vote_set', full=True)
    class Meta:
        queryset = Session.objects.all()
        resource_name = 'session'
        allowed_methods = ['get']

class VoteResource(ModelResource):
    session = fields.ForeignKey(SessionResource, 'session')
    member = fields.ForeignKey(MemberResource, 'member')
    class Meta:
        queryset = Vote.objects.all()
        allowed_methods = ['get']
