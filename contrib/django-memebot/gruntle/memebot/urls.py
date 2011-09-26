from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('gruntle.memebot.views',
        url(r'^$', 'index', name='memebot-index'),
        url(r'^scores/$', 'scores', name='memebot-scores'),
        url(r'^profile/$', 'profile', name='memebot-profile'),
        url(r'^browse/$', 'browse', name='memebot-browse'),
        url(r'^content/(?P<publish_id>\d+)/$', 'content', name='memebot-content'),
        )

urlpatterns += patterns('',
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
        )

urlpatterns += patterns('django.contrib.auth.views',
        url('^login/$', 'login', name='auth-login'),
        url('^logout/$', 'logout_then_login', name='auth-logout'),
        )

if settings.DEV_SERVER:
    urlpatterns += patterns('django.views.static',
            (settings.MEDIA_URL_PATTERN, 'serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}))
