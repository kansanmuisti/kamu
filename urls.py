# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from parliament import views as pv

urlpatterns = [
    url(r'^ajax/parliament-activity/$', pv.get_parliament_activity),
    url(r'^ajax/mp-some-activity/$', pv.get_mp_some_activity),

    url(r'^$', pv.main),
    url(r'^session/$', pv.list_sessions),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<item_nr>\d+)/$', pv.show_item),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<item_nr>\d+)/(?P<subitem_nr>\d+)/$', pv.show_item),

    url(r'^member/$', pv.list_members),
    url(r'^member/(?P<member>[-\w]+)/$', pv.show_member),
    url(r'^member/(?P<member>[-\w]+)/(?P<page>[-\w]+)/$', pv.show_member),

    url(r'^party/$', pv.list_parties),
    url(r'^party/(?P<abbreviation>[-\w]+)/$', pv.show_party_feed),
    url(r'^party/(?P<abbreviation>[-\w]+)/mps/$', pv.show_party_mps),
    url(r'^party/(?P<abbreviation>[-\w]+)/committees/$', pv.show_party_committees),

    url(r'^topic/$', pv.list_topics),
    url(r'^topic/(?P<topic>\d+)-(?P<slug>[-\w]+)/$', pv.show_topic),
    url(r'^topic_by_name/$', pv.show_topic_by_name),

    url(r'^document/(?P<slug>[-\w]+)/$', pv.show_document),

    url(r'^info/$', pv.show_general_info),

    url(r'^search/$', pv.search),
]


# A hack to automatically take name of the callback function as the
# url name. Seems to be compatible with the older stuff.
def hackpattern(pattern):
    return url(pattern.regex.pattern, pattern.callback, name=pattern.lookup_str)
urlpatterns = list(map(hackpattern, urlpatterns))


urlpatterns += [
    url(r'^contact/', include('envelope.urls')),
]


from tastypie.api import Api
from parliament.api import all_resources
from social.api import UpdateResource, FeedResource

v1_api = Api(api_name='v1')
for res in all_resources:
    v1_api.register(res())
v1_api.register(FeedResource())

urlpatterns += [
    url(r'^api/', include(v1_api.urls)),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
