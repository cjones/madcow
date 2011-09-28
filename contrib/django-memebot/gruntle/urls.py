"""Site URL config"""

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
        url(settings.SITE_PATTERN, include('gruntle.memebot.urls')),
        )

