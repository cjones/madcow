#!/usr/bin/env python

"""
Generate random figlet of the ultimate insult!
"""

import sys
import re
from include.pyfiglet import Figlet
from include.colorlib import ColorLib
import random

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*yourmom\s*$')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'yourmom - random figlet of the ultimate insult'

		zipfile = '%s/modules/include/fonts.zip' % dir
		self.figlet = Figlet(zipfile=zipfile)
		self.colorlib = ColorLib(type='mirc')

		# pre-approved list of fonts to use
		self.fonts = (
			'5lineoblique', 'acrobatic', 'alligator', 'alligator2', 'asc_____',
			'ascii___', 'avatar', 'big', 'bigchief', 'block', 'bubble', 'bulbhead',
			'chunky', 'colossal', 'computer', 'cosmic', 'crawford', 'cursive',
			'digital', 'dotmatrix', 'double', 'drpepper', 'eftifont',
			'eftirobot', 'eftiwall', 'eftiwater', 'epic', 'fourtops', 'fuzzy',
			'goofy', 'graceful', 'gradient', 'graffiti', 'hollywood', 'invita',
			'italic', 'larry3d', 'lean', 'maxfour', 'mini', 'nvscript', 'o8',
			'pawp', 'pepper', 'puffy', 'rectangles', 'shadow', 'slant', 'small',
			'smkeyboard', 'smshadow', 'smslant', 'speed', 'stampatello',
			'standard', 'straight', 'twopoint'
		)


	# function to generate a response
	def response(self, *args, **kwargs):
		try:
			self.figlet.setFont(font=random.choice(self.fonts))
			text = self.figlet.renderText('your mom')
			style = random.choice(self.colorlib.rainbowStyles)
			text = self.colorlib.rainbow(text=text, style=style)
			return text


		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: your mom :(' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match(dir='..')
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
