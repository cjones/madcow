#!/usr/bin/env python

# Use AV's babel translator for language conversion

import sys
import re
import urllib

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*(list languages|translate)(?:\s+from\s+(\w+)\s+to\s+(\w+)\s*[-:]\s*(.+))?$', re.I)
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'list languages - list translate languages available'

		self.translated = re.compile('<td bgcolor=white class=s><div style=padding:10px;>(.*?)</div></t')
		self.languages = {	'chinese-simp'  : 'zh',
					'chinese-trad'  : 'zt',
					'chinese'	: 'zh',
					'dutch' 	: 'nl',
					'english'       : 'en',
					'french'        : 'fr',
					'german'        : 'de',
					'greek' 	: 'el',
					'italian'       : 'it',
					'japanese'      : 'ja',
					'korean'        : 'ko',
					'portuguese'    : 'pt',
					'russian'       : 'ru',
					'spanish'       : 'es', }


	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		args = kwargs['args']

		try:
			if args[0] == 'list languages': return '%s: %s' % (nick, ', '.join(self.languages.keys()))

			try:
				fromLang = self.languages[args[1].lower()]
				toLang = self.languages[args[2].lower()]
			except:
				return "%s: I don't know that language, try: list languages" % nick

			url = 'http://babelfish.altavista.com/tr?' + urllib.urlencode(
					{	'doit'		: 'done',
						'intl'		: 1,
						'tt'		: 'urltext',
						'trtext'	: args[3],
						'lp'		: '%s_%s' % (fromLang, toLang),
						'btnTrTxt'	: 'Translate',	}
					)


			return '%s: %s' % (nick, self.translated.search(urllib.urlopen(url).read()).group(1))
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: I couldn't make that translation for some reason :/" % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
