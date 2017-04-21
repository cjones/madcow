from __future__ import unicode_literals

from django.conf.urls import include, url

import django.contrib.auth.views
import memebot.views.accounts
import memebot.views.memebot
import memebot.views.root

urlpatterns = [
    url('^accounts/login/$', django.contrib.auth.views.login, name='accounts-login'),
    url('^accounts/logout/$', django.contrib.auth.views.logout_then_login, name='accounts-logout'),
    url(r'^accounts/profile/$', memebot.views.accounts.view_profile, name='accounts-view-profile'),
    url(r'^accounts/profile/edit/$', memebot.views.accounts.edit_profile, name='accounts-edit-profile'),
    url(r'^memebot/$', memebot.views.memebot.view_index, name='memebot-view-index'),
    url(r'^memebot/scores/$', memebot.views.memebot.view_scores, name='memebot-view-scores'),
    url(r'^memebot/browse/$', memebot.views.memebot.browse_links, name='memebot-browse-links'),
    url(r'^memebot/link/$', memebot.views.memebot.check_link, name='memebot-check-link'),
    url(r'^memebot/link/(?P<publish_id>\d+)/$', memebot.views.memebot.view_link, name='memebot-view-link'),
    url(r'^memebot/link/(?P<publish_id>\d+)/content/$', memebot.views.memebot.view_link_content, name='memebot-view-link-content'),
    url(r'^memebot/rss/$', memebot.views.memebot.view_rss_index, name='memebot-view-rss-index'),
    url(r'^memebot/rss/(?P<name>[a-zA-Z0-9_]+).xml$', memebot.views.memebot.view_rss, name='memebot-view-rss'),
    # url(r'^$', memebot.views.root.view_index, name='root-view-index'),
    url(r'^robots.txt$', memebot.views.root.view_robots, name='root-view-robots'),
    url(r'^calc$', memebot.views.root.view_calc, name='root-view-calc'),
    url('^(?:memebot|accounts|admin)/', memebot.views.root.friendly_404, name='root-friendly-404'),
    url('', memebot.views.root.harsh_404, name='root-harsh-404'),
]
