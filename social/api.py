from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields
from social.models import *

class FeedResource(ModelResource):
    class Meta:
        queryset = Feed.objects.all()
        resource_name = 'social_feed'
        excludes = ['update_error_count']
        filtering = {
            'origin_id': ALL,
            'interest': ALL,
            'account_name': ALL,
            'type': ALL,
        }

class UpdateResource(ModelResource):
    feed = fields.ToOneField('social.api.FeedResource', 'feed')
    class Meta:
        queryset = Update.objects.all().order_by('-created_time')
        resource_name = 'social_update'
        filtering = {
            'feed': ALL_WITH_RELATIONS,
            'type': ALL,
            'text': ALL,
            'sub_type': ALL,
            'created_time': ALL,
            'origin_id': ('exact',),
            'interest': ALL,
        }
