"""Site URL config"""

from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
        url(r'^memebot/', include('gruntle.memebot.urls.memebot')),
        url(r'^accounts/', include('gruntle.memebot.urls.accounts')),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
        )

'''
XXX dunno about this shit
from django.conf import settings
if settings.DEV_SERVER:
    urlpatterns += patterns('django.views.static',
            (settings.MEDIA_URL_PATTERN, 'serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}))
'''
