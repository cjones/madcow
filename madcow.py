#!/usr/bin/env python

__version__ ='1.0.2'

__copyright__ = """
Copyright (C) 2007 Christopher Jones <cjones@insub.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

(see LICENSE for full details)
"""

import sys
import os
from ConfigParser import ConfigParser
from optparse import OptionParser
import re
import threading
import time

class MadcowError(Exception):
	"""
	Abstract base class for madcow runtime problems
	"""
	def __init__(self, error=None):
		self.error = error

	def __str__(self):
		return self.error

class MadcowProtocolError(MadcowError):
	"""
	Problem with underlying protocol handling
	"""

class Madcow(object):
	def __init__(self, config=None, dir=None, verbose=False):
		self.config = config
		self.dir = dir
		self.verbose = verbose

		self.ns = self.config.modules.dbnamespace
		self.ignoreModules = [ '__init__', 'template' ]
		self.moduleDir = self.dir + '/modules'
		self.outputLock = threading.RLock()

		# dynamically generated content
		self.usageLines = []
		self.modules = {}
		self.loadModules()

	def status(self, msg=None):
		if msg is not None and self.verbose is True:
			print '[%s] %s' % (time.asctime(), msg.strip())

	def start(self):
		pass

	def output(self, message):
		pass

	def botName(self):
		pass

	"""
	Dynamic loading of module extensions. This looks for .py files in
	The module directory. They must be well-formed (based on template.py).
	If there are any problems loading, it will skip them instead of crashing.
	"""
	def loadModules(self):
		self.modules = {}

		try: disabled = re.split('\s*[,;]\s*', self.config.modules.disabled)
		except: disabled = []

		if len(disabled) == 0: self.status('No modules are disabled')
		else: self.status('The following modules will not be loaded: %s' % ', '.join(disabled))

		for base, subdirs, files in os.walk(self.moduleDir):
			self.status('*** Reading modules from %s' % base)
			for file in files:
				if file.endswith('.py') is False: continue
				moduleName = file[:-3]

				if moduleName in self.ignoreModules:
					continue

				if moduleName in disabled:
					self.status('* Skipping %s because it is disabled in config' % moduleName)
					continue


				try:
					module = __import__('modules.%s' % moduleName)
					exec 'obj = module.%s.match(config=self.config, ns=self.ns, dir=self.dir)' % moduleName

					if obj is None: raise Exception, 'no match() class'
					if obj.enabled is False: raise Exception, 'disabled'

					try:
						if obj.help is not None:
							self.usageLines.append(obj.help)

					except: pass

					self.status('* Loaded module %s' % moduleName)
					self.modules[moduleName] = obj

				except Exception, e:
					self.status("WARN: Couldn't load module %s: %s" % (moduleName, e))

			# don't recurse
			break


	# checks if we're being addressed and if so, strips that out
	def checkAddressing(self, message):
		addressed = False
		correction = False
		feedback = False
		nick = self.botName()

		# compile regex based on current nick
		self.correction = re.compile('^\s*no,?\s*%s\s*[,:> -]+\s*(.+)' % nick, re.I)
		self.addressed = re.compile('^\s*%s\s*[,:> -]+\s*(.+)' % nick, re.I)
		self.feedback = re.compile('^\s*%s\s*\?+$' % nick, re.I)

		# correction: "no, bot, foo is bar"
		try:
			message = self.correction.search(message).group(1)
			correction = True
			addressed = True
		except: pass

		# bot ping: "bot?"
		if self.feedback.search(message): feedback = True

		# addressed
		try:
			message = self.addressed.search(message).group(1)
			addressed = True
		except: pass

		return addressed, correction, feedback, message

	# returns our help data as a string
	def usage(self):
		return '\n'.join(self.usageLines)

	def processThread(self, *args, **kwargs):
		obj = args[0]
		output = args[1]
		nick = kwargs['nick']

		response = obj.response(nick, **kwargs)
		if response is not None:
			self.outputLock.acquire()
			try: output(response)
			except: pass
			self.outputLock.release()


	# actually process messages!
	def processMessage(self, message, nick, channel, private, output):
		addressed, correction, feedback, message = self.checkAddressing(message)
		if private is True: addressed = True

		### BUILTIN METHODS ###

		# user pinging bot
		if feedback is True:
			output('yes?')
			return

		# display usage
		if message.lower() == 'help':
			output(self.usage())
			return


		### DYNAMIC MODULES ###

		for moduleName, obj in self.modules.iteritems():
			if obj.requireAddressing and addressed is not True: continue

			try: matchGroups = obj.pattern.search(message).groups()
			except: continue

			kwargs = {
				'nick'		: nick,
				'channel'	: channel,
				'addressed'	: addressed,
				'correction'	: correction,
				'args'		: matchGroups,
			}

			if self.allowThreading is True and obj.thread is True:
				t = threading.Thread(target=self.processThread, args=(obj, output), kwargs=kwargs)
				t.start()
			else:
				response = obj.response(**kwargs)
				if response is not None: output(response)


"""
Class to handle configuration directives. Usage is: config.module.attribute
module maps to the headers in the configuration file. It automatically
translates floats and integers to the appropriate type.
"""
class Config(object):
	def __init__(self, file=None, section=None, opts=None):
		if file is not None:
			cfg = ConfigParser()
			cfg.read(file)

			for section in cfg.sections():
				obj = Config(section=section, opts=cfg.items(section))
				setattr(self, section, obj)

		else:
			isInt = re.compile('^[0-9]+$')
			isFloat = re.compile('^[0-9.]+$')
			isTrue = re.compile('^\s*(true|yes|on|1)\s*$')
			isFalse = re.compile('^\s*(false|no|off|0)\s*$')

			for key, val in opts:
				if isInt.search(val): val = int(val)
				elif isFloat.search(val): val = float(val)
				elif isTrue.search(val): val = True
				elif isFalse.search(val): val = False
				setattr(self, key, val)




"""
Standard method of daemonizing on POSIX systems
"""
def detach():
	if os.name != 'posix': return
	if os.fork() > 0: sys.exit(0)
	os.setsid()
	if os.fork() > 0: sys.exit(0)
	for fd in sys.stdout, sys.stderr: fd.flush()
	si = file('/dev/null', 'r')
	so = file('/dev/null', 'a+')
	se = file('/dev/null', 'a+', 0)
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())


"""
Entry point to set up bot and run it
"""
def main(argv=None):
	# where we are being run from
	dir = os.path.abspath(os.path.dirname(sys.argv[0]))

	# parse commandline options
	parser = OptionParser(version=__version__)
	parser.add_option(	'-c', '--config', default=dir + '/madcow.ini',
				help='use FILE for config (default: %default)', metavar='FILE' )

	parser.add_option(	'-d', '--detach', action='store_true', default=False,
				help='detach when run (default: %default)' )

	parser.add_option(	'-v', '--verbose', action='store_true', default=False,
				help='turn on verbose output (default: %default)' )

	parser.add_option(	'-p', '--protocol',
				help='force the use of this output protocol' )

	opts, args = parser.parse_args()

	# read config file
	config = Config(file=opts.config)

	# load specified protocol
	if opts.protocol is not None: protocol = opts.protocol
	else: protocol = config.main.module

	try:
		exec 'from %s import ProtocolHandler' % protocol
	except Exception, e:
		raise MadcowProtocolError, "couldn't load %s: %s" % (protocol, e)

	# daemonize if requested (and on a posix system)
	if config.main.detach is True or opts.detach is True: detach()

	# run bot
	bot = ProtocolHandler(config=config, dir=dir, verbose=opts.verbose)
	bot.start()

	return 0


if __name__ == '__main__': sys.exit(main())
