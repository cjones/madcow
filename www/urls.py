# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *
import www.settings

urlpatterns = patterns('',
    # admin interface
    #(r'^admin/',                include('django.contrib.admin.urls')),

    # search form
    (r'^search/$',                'www.memebot.views.search'),
    (r'^search/(?P<page>\d+)/$',        'www.memebot.views.search'),

    # author views
    (r'^author/$',                'www.memebot.views.authors'),
    (r'^author/top/$',            'www.memebot.views.top'),
    (r'^author/(?P<id>\d+)/$',        'www.memebot.views.author'),
    (r'^author/(?P<id>\d+)/(?P<img>img)/$',    'www.memebot.views.author'),
    (r'^author/(?P<id>\d+)/(?P<youtube>youtube)/$',    'www.memebot.views.author'),

    # url list views
    (r'^$',                    'www.memebot.views.url'),
    (r'^url/(?P<page>\d+)/$',        'www.memebot.views.url'),
    (r'^url/(?P<page>\d+)/(?P<img>img)/$',    'www.memebot.views.url'),
    (r'^url/(?P<page>\d+)/(?P<youtube>youtube)/$',    'www.memebot.views.url'),

    # static content
    (r'^static/(?P<path>.*)$',        'django.views.static.serve',
                        {'document_root' : www.settings.MADCOW_STATIC }),

    # memecheck
    (r'^memecheck/$',            'www.memebot.views.memecheck'),
    (r'^memecheck/(?P<result>result)/$',    'www.memebot.views.memecheck'),

    # everything else redirects to root
    (r'.*',                    'www.memebot.views.root'),
)
