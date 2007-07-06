#!/usr/bin/env python

# Get a weather report from wunderground


import sys
import re
import urllib
import learn
import os

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*(?:fc|forecast|weather)(?:\s+(.*)$)?')
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.ns = ns
		if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
		self.dir = dir
		self.help = 'fc <location> - look up forecast for location'
		self.help = self.help + '\nfc @nick - lookup forecast for this nick\'s location'
		self.help = self.help + '\nlearn <nick> <location> - permanently learn a nick\'s location'

		self.lookup = re.compile('^@(\S+)')
		self.resultType = re.compile('(Click on a column heading|Current Conditions|There has been an error)')
		self.multipleResults = re.compile('<td class="sortC"><a href="([^>]+)">([^<]+)')
		self.baseURL = 'http://www.wunderground.com'

		self.tempF = re.compile('<nobr><b>([0-9.]+)</b>&nbsp;&#176;F</nobr>')
		self.tempC = re.compile('<nobr><b>([0-9.]+)</b>&nbsp;&#176;C</nobr>')
		self.skies = re.compile('<div id="b" style="font-size: 14px;">(.*?)</div>')
		self.cityName = re.compile('<h1>(.*?)</h1>')
		self.humidity = re.compile('pwsvariable="humidity".*?><nobr><b>([0-9.]+%)</b></nobr></span></td>')
  		self.windSpeed = re.compile('<nobr><b>([0-9.]+)</b>&nbsp;mph</nobr>')
  		self.windDir = re.compile('[0-9.]+&deg;</span>\s*\(([NSEW]+)\)</td>')

	def norm(self, text):
		return ' '.join(text.split()).lower()

	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']

		try: arg = ' '.join(kwargs['args'][0].split())
		except: arg = None

		# if empty = lookup loc of 'nick'
		# elif @foo = lookup loc of 'foo'
		# else lookup query directly

		lookup = query = None
		if arg is None or arg == '':
			lookup = nick
		elif arg.startswith('@'):
			lookup = arg[1:]
		else:
			query = arg

		if lookup is not None:
			l = learn.match(ns=self.ns, dir=self.dir)
			query = l.lookup(lookup)

			if query is None:
				return "I don't know where %s lives, try: learn %s <location>" % (lookup, lookup)


		try:
			response = None

			queryString = urllib.urlencode( { 'query' : query } )
			url = '%s/cgi-bin/findweather/getForecast?%s' % (self.baseURL, queryString)

			while True:
				doc = urllib.urlopen(url).read()
				mo = self.resultType.search(doc)
				if mo: type = mo.group(1)
				else: type = 'There has been an error'

				# found multiple items
				if type == 'Click on a column heading':
					results = [(path, city) for path, city in self.multipleResults.findall(doc)]
					if len(results) == 1:
						url = self.basURL + results[0][0]
					elif len(results) > 1:
						d = {}
						for u, l in results:
							d[self.norm(l)] = u

						if len(d) == 1:
							url = self.baseURL + d[list(d)[0]]

						elif d.has_key(self.norm(query)):
							url = self.baseURL + d[self.norm(query)]
						else:
							response = 'I found multiple results: ' + '; '.join([city for path, city in results])

				# proper page
				elif type == 'Current Conditions':
					try: cityName = self.cityName.search(doc).group(1).strip()
					except: cityName = query

					try: tempF = str(int(round(float(self.tempF.search(doc).group(1))))) + 'F'
					except: tempF = None

					try: tempC = str(int(round(float(self.tempC.search(doc).group(1))))) + 'C'
					except: tempC = None

					try: skies = self.skies.search(doc).group(1)
					except: skies = None

					try: humidity = self.humidity.search(doc).group(1)
					except: humidity = None

					try: windSpeed = self.windSpeed.search(doc).group(1) + 'mph'
					except: windSpeed = None

					try: windDir = self.windDir.search(doc).group(1)
					except: windDir = None

					output = []

					if tempF or tempC:
						temps = []
						if tempF: temps.append(tempF)
						if tempC: temps.append(tempC)
						output.append('/'.join(temps))

					if humidity:
						output.append('humidity: %s' % humidity)

					if windSpeed and windDir:
						output.append('%s at %s' % (windDir, windSpeed))

					if skies:
						output.append(skies)

					response = '%s: %s' % (cityName, ', '.join(output))

				# nothing found
				elif type == 'There has been an error':
					response = "I couldn't find %s" % query

				if response: break
			
			return '%s: %s' % (nick, response)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: There is no weather there' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
