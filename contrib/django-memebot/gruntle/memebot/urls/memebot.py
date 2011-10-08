"""MemeBot URL config"""

from django.conf.urls.defaults import *

urlpatterns = patterns('gruntle.memebot.views.memebot',
        url(r'^$', 'view_index', name='memebot-view-index'),
        url(r'^scores/$', 'view_scores', name='memebot-view-scores'),
        url(r'^browse/$', 'browse_links', name='memebot-browse-links'),
        url(r'^link/$', 'check_link', name='memebot-check-link'),
        url(r'^link/(?P<publish_id>\d+)/$', 'view_link', name='memebot-view-link'),
        url(r'^link/(?P<publish_id>\d+)/content/$', 'view_link_content', name='memebot-view-link-content'),
        url(r'^rss/$', 'view_rss_index', name='memebot-view-rss-index'),
        url(r'^rss/(?P<name>[a-zA-Z0-9_]+).xml$', 'view_rss', name='memebot-view-rss'),
        )
