from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('facebook.views',
    url(r'^connect/$', 'connect', name='facebook_connect'),
    url(r'^register/form/$', 'register_form', name='facebook_register_form'),
)
