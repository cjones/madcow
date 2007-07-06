from django.conf.urls.defaults import *
import www.settings

urlpatterns = patterns('',
	# admin interface
	#(r'^admin/',				include('django.contrib.admin.urls')),

	# search form
	(r'^search/$',				'www.memebot.views.search'),
	(r'^search/(?P<page>\d+)/$',		'www.memebot.views.search'),

	# author views
	(r'^author/$',				'www.memebot.views.authors'),
	(r'^author/top/$',			'www.memebot.views.top'),
	(r'^author/(?P<id>\d+)/$',		'www.memebot.views.author'),
	(r'^author/(?P<id>\d+)/(?P<img>img)/$',	'www.memebot.views.author'),
	(r'^author/(?P<id>\d+)/(?P<youtube>youtube)/$',	'www.memebot.views.author'),

	# url list views
	(r'^$',					'www.memebot.views.url'),
	(r'^url/(?P<page>\d+)/$',		'www.memebot.views.url'),
	(r'^url/(?P<page>\d+)/(?P<img>img)/$',	'www.memebot.views.url'),
	(r'^url/(?P<page>\d+)/(?P<youtube>youtube)/$',	'www.memebot.views.url'),

	# static content
	(r'^static/(?P<path>.*)$',		'django.views.static.serve',
						{'document_root' : www.settings.MADCOW_STATIC }),

	# memecheck
	(r'^memecheck/$',			'www.memebot.views.memecheck'),
	(r'^memecheck/(?P<result>result)/$',	'www.memebot.views.memecheck'),

	# everything else redirects to root
	(r'.*',					'www.memebot.views.root'),
)
