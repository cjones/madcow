from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('gruntle.memebot.views',
        url(r'^$', 'index', name='index'),
        url(r'^scores/$', 'scores', name='scores'),
        url(r'^profile/$', 'profile', name='profile'),
        url(r'^browse/$', 'browse', name='browse'),
        url(r'^content/(?P<link_id>\d+)/$', 'content', name='content'),
        )

urlpatterns += patterns('',
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
        )

urlpatterns += patterns('django.contrib.auth.views',
        url('^login/$', 'login', name='login'),
        url('^logout/$', 'logout_then_login', name='logout'),
        )
