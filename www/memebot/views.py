from django.http import HttpResponse, HttpResponseRedirect
from www.memebot.models import *
import www.settings
from django.template import Context, loader
import datetime
import os
from django.core.cache import cache
import re
from django.db.models import Q
from django.utils.html import escape
from urllib import urlencode

def root(request, *args, **kwargs):
	return HttpResponseRedirect('/url/1')

def url(request, *args, **kwargs):
	"""
	Perform some sanity checking
	"""
	if kwargs.has_key('page'):
		page = int(kwargs['page'])
	else:
		return HttpResponseRedirect('/url/1/')

	if page < 1 or page > 365:
		return HttpResponseRedirect('/url/1/')



	"""
	Calculate date range to show and load those URLs up
	"""
	start = datetime.date.today() - datetime.timedelta(days=(page-1))
	end   = start + datetime.timedelta(days=1)
	urls = URL.objects.filter(posted__range=(start, end)).order_by('-id')

	"""
	Image filter
	"""
	toggles = [
		'<a href="/url/%s/img/">Images Only</a>' % page,
		'<a href="/url/%s/youtube/">YouTube Only</a>' % page,
	]

	filter = None
	if kwargs.has_key('img'):
		urls = urls.filter(
			Q(url__endswith='.jpg')  |
			Q(url__endswith='.jpeg') |
			Q(url__endswith='.gif')  |
			Q(url__endswith='.tiff') |
			Q(url__endswith='.png')
		)

		toggles = ['<a href="/url/%s/">All Links</a>' % page]
		filter = 'img'

	elif kwargs.has_key('youtube'):
		urls = urls.filter(url__contains='youtube.com')
		toggles = ['<a href="/url/%s/">All Links</a>' % page]
		filter = 'youtube'


	"""
	These are for navigation links
	"""
	date = start.strftime('%A, %B %d, %Y')

	if page == 1:
		newer = None
		today = None
	else:
		newer = '/url/' + str(page - 1)
		today = '/url/1'

	if page == 2:
		newer = None

	older = '/url/' + str(page + 1)

	if filter is not None:
		if older is not None:
			older += '/%s' % filter

		if newer is not None:
			newer += '/%s' % filter

		if today is not None:
			today += '/%s' % filter

	"""
	Render content and return
	"""
	t = loader.get_template('index.html')
	c = Context({
		'urls'	: urls,
		'date'	: date,

		'older'	: older,
		'today'	: today,
		'newer'	: newer,
		'toggles': toggles,
	})
	return HttpResponse(t.render(c))


def authors(request, *args, **kwargs):
	authors = cache.get('authors')
	if authors is None:
		authors = [(a, a.count) for a in Author.objects.all()]
		authors = sorted(authors, lambda x, y: cmp(y[1], x[1]))
		cache.set('authors', authors, 900)

	if kwargs.has_key('top'):
		authors = authors[:kwargs['top']]
		top = True
	else:
		top = False

	t = loader.get_template('authors.html')
	c = Context({
		'authors'	: authors,
		'top'		: top,
	})

	return HttpResponse(t.render(c))

def top(request, *args, **kwargs):
	return authors(request, top=10)


def author(request, *args, **kwargs):
	try:
		author = Author.objects.get(id=int(kwargs['id']))
	except:
		return HttpResponseRedirect('/author/')


	urls = author.url_set.order_by('-id')

	toggles = [
		'<a href="/author/%s/img/">Images Only</a>' % kwargs['id'],
		'<a href="/author/%s/youtube/">YouTube Only</a>' % kwargs['id'],
	]

	filter = None
	if kwargs.has_key('img'):
		urls = urls.filter(
			Q(url__endswith='.jpg')  |
			Q(url__endswith='.jpeg') |
			Q(url__endswith='.gif')  |
			Q(url__endswith='.tiff') |
			Q(url__endswith='.png')
		)

		toggles = ['<a href="/author/%s/">All Links</a>' % kwargs['id']]
		filter = 'img'

	elif kwargs.has_key('youtube'):
		urls = urls.filter(url__contains='youtube.com')
		toggles = ['<a href="/author/%s/">All Links</a>' % kwargs['id']]
		filter = 'youtube'


	t = loader.get_template('author.html')
	c = Context({
		'author'	: author,
		'urls'		: urls,
		'toggles'	: toggles,
	})

	return HttpResponse(t.render(c))


def search(request, *args, **kwargs):
	t = loader.get_template('search_results.html')

	resultsPerPage = 25
	maxPages = 35

	"""
	if any part of this encountrs an exception, be
	sure to return a friendly "no results found" page
	"""
	try:
		term = request.GET['q']
		if len(term) == 0: raise Exception, 'No query specified'

		"""
		To prevent unnecessary DB grinding, only calculate
		the results of a particular query once every 5 minutes.
		This allows the user to sift through pages of results
		without executing the query again every time.
		"""
		cacheKey = 'search_' + term
		results = cache.get(cacheKey)

		if results is None:
			results = URL.objects.filter(
				Q(url__icontains=term) |
				Q(clean__icontains=term) |
				Q(author__name__icontains=term)
				).order_by('-id')[:(resultsPerPage * maxPages)]

			"""
			Force evaluation and then cache it. Otherwise it
			would just cache the QuerySet, which isn't helpful
			"""
			results = list(results)
			cache.set(cacheKey, results, 300)


		# what page does the user want? if unspecified, start at 1
		if kwargs.has_key('page'): page = int(kwargs['page'])
		else: page = 1

		# calculate how many pages exist
		resultSize = len(results)
		pages = resultSize / resultsPerPage
		if (resultSize % resultsPerPage): pages += 1

		# boundary check on requested page
		if page < 1: page = 1
		if page > pages: page = pages

		# calculate which part of the resultset to show
		start = (page - 1) * resultsPerPage
		end = start + resultsPerPage
		if end > resultSize: end = resultSize
		results = results[start:end]


		# construct page navigation bar
		if pages > 1:
			navbar = []
			for p in range(1, pages+1):
				if p == page: link = '<b><u>%s</u></b>' % p
				else: link = '<a href="/search/%s/?%s">%s</a>' % (p, urlencode({'q': term}), p)
				navbar.append(link)

			navbar = '&nbsp;'.join(navbar)
		else:
			navbar = None


		"""
		Render content and return
		"""

		c = Context({
			'results':	results,
			'pages':	pages,
			'start':	(start + 1),
			'end':		end,
			'total':	resultSize,
			'term':		term,
			'navbar':	navbar,
		})

		return HttpResponse(t.render(c))

	except Exception, e:
		return HttpResponse(t.render(Context({ 'error' : e })))


def memecheck(request, *args, **kwargs):
	try:
		url = request.GET['url']
		results = URL.objects.filter(url__iexact=url).order_by('-id')[:1]
		if results.count() > 0:
			result = results[0]
			response = 'OLD MEME. First posted by %s on %s' % (result.author.name, result.posted)
			response = '<span class="oldmeme">%s</span>' % response
		else:
			response = '<span class="newmeme">NEW MEME</span>'

	except:
		url = 'url'
		response = None

	try:
		if int(request.GET['clean']) == 1: clean = 1
		else: clean = None
	except:
		clean = None

	bookmarklet = 'javascript:( function() { var url = \'http://memebot.gruntle.org/memecheck/?clean=1&url=\' + escape(window.location.href); var name = \'memecheck\'; var params = \'width=588,height=156,toolbar=0,status=1,location=0,scrollbars=0,menubar=0,resizable=0\'; window.open(url, name, params); })();'

	toggles = [ '<a href="%s">Bookmarklet</a>' % bookmarklet ]

	t = loader.get_template('memecheck.html')
	c = Context({
		'url':		url,
		'response':	response,
		'clean':	clean,
		'toggles':	toggles,
	})

	return HttpResponse(t.render(c))
