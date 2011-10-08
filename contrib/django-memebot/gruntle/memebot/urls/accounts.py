"""Accounts URL config"""

from django.conf.urls.defaults import *

urlpatterns = patterns('django.contrib.auth.views',
        url('^login/$', 'login', name='accounts-login'),
        url('^logout/$', 'logout_then_login', name='accounts-logout'),
        )

urlpatterns += patterns('gruntle.memebot.views.accounts',
        url(r'^profile/$', 'view_profile', name='accounts-view-profile'),
        url(r'^profile/edit/$', 'edit_profile', name='accounts-edit-profile'),
        )
