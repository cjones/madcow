"""MemeBot URL config"""

from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('gruntle.memebot.views',
        url(r'^$', 'index', name='index'),
        url(r'^scores/$', 'scores', name='scores'),
        url(r'^profile/$', 'profile', name='profile'),
        url(r'^browse/$', 'browse', name='browse'),
        url(r'^link/(?P<publish_id>\d+)/content/$', 'view_content', name='view-content'),
        url(r'^link/(?P<publish_id>\d+)/$', 'view_link', name='view-link'),
        url(r'^rss/(?P<name>[a-zA-Z0-9_]+)/$', 'view_rss', name='view-rss'),
        url(r'^rss/$', 'rss_index', name='rss-index'),
        )

urlpatterns += patterns('',
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
        )

urlpatterns += patterns('django.contrib.auth.views',
        url('^login/$', 'login', name='auth-login'),
        url('^logout/$', 'logout_then_login', name='logout'),
        )

if settings.DEV_SERVER:
    urlpatterns += patterns('django.views.static',
            (settings.MEDIA_URL_PATTERN, 'serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}))
