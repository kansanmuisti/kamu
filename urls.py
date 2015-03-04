# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

#from django.contrib import admin
#admin.autodiscover()

# Change the length of EmailFields to accommodate overlong
# Facebook email addresses.
from django.db.models.fields import EmailField, CharField
def email_field_init(self, *args, **kwargs):
  kwargs['max_length'] = kwargs.get('max_length', 200)
  CharField.__init__(self, *args, **kwargs)
EmailField.__init__ = email_field_init

#urlpatterns = patterns('',
#    (r'^admin/', include(admin.site.urls)),
#)

urlpatterns = patterns('parliament.views',
    url(r'^$', 'main'),
    url(r'^ajax/parliament-activity/$', 'get_parliament_activity'),
    url(r'^ajax/mp-some-activity/$', 'get_mp_some_activity'),

    url(r'^session/$', 'list_sessions'),
    url(r'^session/calendar/(?P<month>\d+)-(?P<year>\d+)/$', 'list_sessions'),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<item_nr>\d+)/$', 'show_item'),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<item_nr>\d+)/(?P<subitem_nr>\d+)/$', 'show_item'),

    url(r'^member/$', 'list_members'),
    url(r'^member/(?P<member>[-\w]+)/$', 'show_member'),
    url(r'^member/(?P<member>[-\w]+)/(?P<page>[-\w]+)/$', 'show_member'),

    url(r'^party/$', 'list_parties'),
    url(r'^party/(?P<abbreviation>[-\w]+)/$', 'show_party_feed'),
    url(r'^party/(?P<abbreviation>[-\w]+)/mps/$', 'show_party_mps'),
    url(r'^party/(?P<abbreviation>[-\w]+)/committees/$', 'show_party_committees'),

    url(r'^topic/$', 'list_topics'),
    url(r'^topic/(?P<topic>\d+)-(?P<slug>[-\w]+)/$', 'show_topic'),

    url(r'^document/(?P<slug>[-\w]+)/$', 'show_document'),

    url(r'^search/$', 'search'),
)

from tastypie.api import Api
from parliament.api import all_resources
from social.api import UpdateResource, FeedResource

v1_api = Api(api_name='v1')
for res in all_resources:
    v1_api.register(res())
v1_api.register(FeedResource())

urlpatterns += patterns('',
    url(r'^api/', include(v1_api.urls)),
)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
