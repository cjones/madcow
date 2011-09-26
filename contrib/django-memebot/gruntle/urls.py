"""Root URL config"""

import os

from django.conf.urls.defaults import *
from django.conf import settings

def mkpat(path):
    """Normalize path to expected pattern"""
    path = os.path.join(os.path.normpath(path), '')
    if path.startswith('/'):
        path = path[1:]
    if path:
        path = '^' + path
    return path

isdev = os.environ.get('DEV_SERVER', 'false') == 'true'

# include memebot's URLs to SITE_ROOT
urlpatterns = patterns('',
        (mkpat(settings.SITE_ROOT) if isdev else '', include('gruntle.memebot.urls')),
        )

# if this is a server run by ./manage.py runserver, serve static media
if isdev:
    urlpatterns = patterns('',
            url(mkpat(settings.MEDIA_URL) + '(?P<path>.*)', 'django.views.static.serve', {
                'document_root': settings.MEDIA_ROOT, 'show_indexes': True}, name='static-media')) + urlpatterns
