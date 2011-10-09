"""Root URL config"""

from django.conf.urls.defaults import *

urlpatterns = patterns('gruntle.memebot.views.root',
        url(r'^$', 'view_index', name='root-view-index'),
        url(r'^robots.txt$', 'view_robots', name='root-view-robots'),
        )
