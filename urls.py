from django.conf.urls.defaults import *
from django.conf import settings
from kamu.users.views import login, logout
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

import djapian
djapian.load_indexes()

# Change the length of EmailFields to accommodate overlong
# Facebook email addresses.
from django.db.models.fields import EmailField, CharField
def email_field_init(self, *args, **kwargs):
  kwargs['max_length'] = kwargs.get('max_length', 200)
  CharField.__init__(self, *args, **kwargs)
EmailField.__init__ = email_field_init

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('votes.views',
    url(r'^session/$', 'list_sessions'),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/tag/$', 'tag_session'),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/user-vote/$', 'set_session_user_vote'),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/(?P<section>[\w]+)/$', 'show_session'),
    url(r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/$', 'show_session'),
    url(r'^session/(?P<plsess>[\w-]+)/statements/(?P<dsc>\d+)/$',
        'show_plsession', {'section': 'statements'}),
    url(r'^session/(?P<plsess>[\w-]+)/$', 'show_plsession'),
    url(r'^plsession/$', 'list_plsessions'),
    url(r'^party/$', 'list_parties'),
    url(r'^member/$', 'list_members'),
    url(r'^member/(?P<member>[-\w]+)/(?P<section>[\w]+)/$', 'show_member'),
    url(r'^member/(?P<member>[-\w]+)/$', 'show_member'),
    url(r'^member/(?P<member>[-\w]+)/user-vote/$', 'set_member_user_vote'),
    url(r'^search/$', 'search'),
    url(r'^search/county/$', 'search_county'),
    url(r'^search/autocomplete/$', 'search_autocomplete'),
    url(r'^search/keyword/$', 'search_by_keyword'),
    url(r'^contact/$', 'about', {'section': 'feedback'}),
    url(r'^contact/sent/$', direct_to_template, {'template': 'contact_form/contact_form_sent.html'},
        name='contact_form_sent'),
    url(r'^about/(?P<section>[\w-]+)/$', 'about'),
    url(r'^$', 'about', {'section': 'main'}),
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

urlpatterns += patterns('opinions.views',
    url(r'^opinions/$', 'list_questions'),
    url(r'^opinions/(?P<source>\w+)/(?P<question>\d+)/$', 'show_question'),
)

urlpatterns += patterns('cms.views',
    url(r'^news/vaalikoneet-avoimiksi/', 'show_news'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }),
    )
