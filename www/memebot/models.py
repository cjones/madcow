# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#	 * Rearrange models' order
#	 * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models
import urlparse
import re

class Author(models.Model):
	name = models.TextField(unique=True)
	points_new = models.IntegerField(null=True, blank=True)
	points_old = models.IntegerField(null=True, blank=True)
	points_credit = models.IntegerField(null=True, blank=True)

	def getCount(self):
		count = self.url_set.count()
		return count

	count = property(getCount)




	def __str__(self):
		return self.name

	class Meta:
		db_table = 'author'

	class Admin:
		pass

class Channel(models.Model):
	name = models.TextField(unique=True)

	def __str__(self):
		return self.name

	class Meta:
		db_table = 'channel'

	class Admin:
		pass


class URL(models.Model):
	url = models.TextField(unique=True)
	clean = models.TextField(unique=True)
	author = models.ForeignKey(Author)
	channel = models.ForeignKey(Channel)
	citations = models.IntegerField(null=True, blank=True)
	posted = models.DateTimeField('date posted')

	def getTruncatedURL(self):
		url = self.url

		max = 55

		if len(url) > max:
			url = url[:max] + '...' + url[-4:]

		return url

	def getTimeStamp(self):
		#return str(self.posted)
		d = self.posted
		time = d.time().isoformat()[:8]
		return time
	

	turl = property(getTruncatedURL)
	stamp = property(getTimeStamp)

	def getSafe(self):
		# XXX i'm sure there's a safe, easy way to do this, but
		# it needed to be done asap since the site is live.
		# this brutally removes any XSS crap or goatse redirects.
		# .. bastards

		uri = urlparse.urlparse(self.url)

		badStuff = re.compile('["><]')

		schema = badStuff.sub('', uri[0])
		host = badStuff.sub('', uri[1])
		path = badStuff.sub('', uri[2])
		query = badStuff.sub('', uri[4])
		frag = badStuff.sub('', uri[5])

		if schema not in ['http', 'https']:
			schema = 'http'

		if path == '': path = '/'


		newURL = '%s://%s%s' % (schema, host, path)

		if len(query) > 0:
			newURL += '?%s' % query

		if len(frag) > 0:
			newURL += '#%s' % frag

		return newURL






	safe = property(getSafe)


	def __str__(self):
		return self.url

	class Meta:
		db_table = 'url'

	class Admin:
		pass


