from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^kamu/', include('kamu.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('votes.views',
    (r'^session/$', 'list_sessions'),
    (r'^session/(?P<plsess>[\w-]+)/$', 'show_plsession'),
    (r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/$', 'show_session'),
    (r'^session/(?P<plsess>[\w-]+)/(?P<sess>\d+)/tag/$', 'tag_session'),
    (r'^plsession/$', 'list_plsessions'),
    (r'^party/$', 'list_parties'),
    (r'^member/$', 'list_members'),
    (r'^member/([-\w]+)/$', 'show_member'),
    (r'^member/([-\w]+)/statement/$', 'list_member_statements'),
    (r'^search/$', 'search'),
    (r'^about/$', 'about'),
    (r'^$', 'main_page'),
)

urlpatterns += patterns('users.views',
    (r'account/register/$', 'register'),
)

urlpatterns += patterns('orgs.views',
    (r'org/add/$', 'add_org'),
    (r'org/$', 'list_orgs'),
    (r'org/(?P<org>[-\w]+)/$', 'show_org'),
    (r'org/(?P<org>[-\w]+)/modify/$', 'modify_org'),
    (r'org/(?P<org>[-\w]+)/modify-score/(?P<plsess>[\w-]+)/(?P<sess>\d+)/$', 'modify_score'),
)

urlpatterns += patterns('',
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^account/login/$', login, {'template_name': 'login.html'}),
    (r'^account/logout/$', logout, {'next_page': '/'}),
    (r'^beta/$', 'kamu.beta.views.register'),
    (r'^beta/thankyou/$', 'kamu.beta.views.thankyou'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }),
    )
