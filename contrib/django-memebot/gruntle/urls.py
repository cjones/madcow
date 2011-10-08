"""Site URL config"""

from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
        url(r'^memebot/', include('gruntle.memebot.urls.memebot')),
        url(r'^accounts/', include('gruntle.memebot.urls.accounts')),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
        url(r'^$', 'gruntle.memebot.views.view_index', name='root-view-index'),
        )

if settings.DEV_SERVER:
    import re
    urlpatterns += patterns('django.views',
            url(r'^%s(?P<path>.*)' % re.escape(settings.MEDIA_URL[1:]), 'static.serve',
                {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
            )
