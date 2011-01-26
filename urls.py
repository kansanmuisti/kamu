from django.conf.urls.defaults import *
from django.conf import settings
from kamu.users.views import login, logout
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

import djapian
djapian.load_indexes()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('votes.views',
    (r'^session/$', 'list_sessions'),
    (r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/tag/$', 'tag_session'),
    (r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/(?P<section>[\w]+)/$', 'show_session'),
    (r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/$', 'show_session'),
    (r'^session/(?P<plsess>[\w-]+)/statements/(?P<dsc>\d+)/$',
     'show_plsession', {'section': 'statements'}),
    (r'^session/(?P<plsess>[\w-]+)/$', 'show_plsession'),
    (r'^plsession/$', 'list_plsessions'),
    (r'^party/$', 'list_parties'),
    (r'^member/$', 'list_members'),
    (r'^member/(?P<member>[-\w]+)/(?P<section>[\w]+)/$', 'show_member'),
    (r'^member/(?P<member>[-\w]+)/$', 'show_member'),
    (r'^search/$', 'search'),
    (r'^search/autocomplete/$', 'search_autocomplete'),
    (r'^search/county/$', 'search_county'),
    url(r'^contact/$', 'about', {'section': 'feedback'}),
    url(r'^contact/sent/$', direct_to_template, {'template': 'contact_form/contact_form_sent.html'},
        name='contact_form_sent'),
    (r'^about/(?P<section>[\w-]+)/$', 'about'),
    (r'^$', 'about', {'section': 'main'}),
)

#urlpatterns += patterns('users.views',
#    (r'account/register/$', 'register'),
#)

# Disable organization support for now.
urlpatterns += patterns('orgs.views',
#    (r'org/add/$', 'add_org'),
#    (r'org/add/preview$', 'preview_add_org'),
    (r'org/$', 'list_orgs'),
#    (r'org/(?P<org>[-\w]+)/$', 'show_org'),
#    (r'org/(?P<org>[-\w]+)/modify/$', 'modify_org'),
#    (r'org/(?P<org>[-\w]+)/modify/preview$', 'preview_modify_org'),
#    (r'org/(?P<org>[-\w]+)/modify-score/(?P<plsess>[\w-]+)/(?P<sess>\d+)/$', 'modify_score'),
)

urlpatterns += patterns('',
    (r'^facebook/', include('facebook.urls')),
)

urlpatterns += patterns('',
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^account/logout/$', logout, name="logout"),
    url(r'^account/login/$', login, name="login"),
    (r'^account/', include('registration.backends.default.urls')),
)

urlpatterns += patterns('', (r'^i18n/', include('django.conf.urls.i18n')))

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }),
    )
