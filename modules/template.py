#!/usr/bin/env python

"""
NOTE: This is the template for creating your own user modules.  Copy this file
to something unique (it must end with .py!).  Edit the __init__ function.  This is
where you set what regular expression will trigger the process() call when run
within the bot, whether it should spawn a new thread when running response(), and whether
addressing is required.

The response() function is where your script goes, it should return a response.
"""

import sys
import re

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		"""
		arguments that this module gets:

		config: the config class. this lets you access stuff in the .ini file

		ns: namespace. if you are saving stuff to a DB file, you should name the file
		     with this in it somewhere. this lets you run multiple bots from the same
		     directory

		dir: this is the directory the bot is run from. this is where you want
		     to store any data files, if necessary

		"""

		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*keyword\s+(\S+)')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = None				# Put your usage line here as a string

	# function to generate a response
	def response(self, *args, **kwargs):

		"""
		kwargs is a dict passed from the bot. this allows you to develop
		more advanced modules that require introspection. the following
		key/value pairs are made available:

		<string>  nick		- nickname of the user invoking the module
		<string>  channel	- channel that module was triggered from
		<boolean> addressed	- True/False, whether bot was addressed by name
		<boolean> correction	- True/False, whether user was correcting the bot
		<list>    args		- list of args trapped from the regex above.
		"""

		nick = kwargs['nick']
		args = kwargs['args']

		try:
			"""
			Your methods go here. You should return a string when you are done,
			or None for no response.  Any excptions will be caught and
			return an error. This is not strictly necessary, the bot will not
			crash if you don't catch these errors. If you want it to silently
			fail, you can remove this try/catch block.
			"""

			return None

		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: I failed to perform that lookup' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
