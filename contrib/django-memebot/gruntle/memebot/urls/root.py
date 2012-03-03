"""Root URL config"""

from django.conf.urls.defaults import *

urlpatterns = patterns('gruntle.memebot.views.root',
        url(r'^$', 'view_index', name='root-view-index'),
        url(r'^robots.txt$', 'view_robots', name='root-view-robots'),
        url(r'^calc$', 'view_calc', name='root-view-calc'),

        # roll our own 404 to get some control over it
        url('^(?:memebot|accounts|admin)/', 'friendly_404', name='root-friendly-404'),
        url('', 'harsh_404', name='root-harsh-404'),
        )
