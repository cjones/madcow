#!/usr/bin/env python

__version__ ='1.0.6'

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
		return 'madcow'

	"""
	Dynamic loading of module extensions. This looks for .py files in
	The module directory. They must be well-formed (based on template.py).
	If there are any problems loading, it will skip them instead of crashing.
	"""
	def loadModules(self):
		try: disabled = re.split('\s*[,;]\s*', self.config.modules.disabled)
		except: disabled = []

		files = os.walk(self.moduleDir).next()[2]
		self.status('[MOD] * Reading modules from %s' % self.moduleDir)

		for file in files:
			if file.endswith('.py') is False: continue
			modName = file[:-3]

			if modName in self.ignoreModules: continue

			if modName in disabled:
				self.status('[MOD] Skipping %s because it is disabled in config' % modName)
				continue

			try:
				module = __import__('modules.' + modName, globals(), locals(), ['match'])
				MatchClass = getattr(module, 'match')
				obj = MatchClass(config=self.config, ns=self.ns, dir=self.dir)

				if obj.enabled is False: raise Exception, 'disabled'

				if hasattr(obj, 'help') and obj.help is not None:
					self.usageLines.append(obj.help)

				self.status('[MOD] Loaded module %s' % modName)
				self.modules[modName] = obj

			except Exception, e:
				self.status("[MOD] WARN: Couldn't load module %s: %s" % (modName, e))


	# pre-processing filter that catches whether the bot is being addressed or not..
	def checkAddressing(self, message=None, params={}):
		params['addressed'] = False
		params['correction'] = False
		params['feedback'] = False
		nick = self.botName()

		# compile regex based on current nick
		self.correction = re.compile('^\s*no,?\s*%s\s*[,:> -]+\s*(.+)' % re.escape(nick), re.I)
		self.addressed = re.compile('^\s*%s\s*[,:> -]+\s*(.+)' % re.escape(nick), re.I)
		self.feedback = re.compile('^\s*%s\s*\?+$' % re.escape(nick), re.I)

		# correction: "no, bot, foo is bar"
		try:
			message = self.correction.search(message).group(1)
			params['correction'] = True
			params['addressed'] = True
		except: pass

		# bot ping: "bot?"
		if self.feedback.search(message):
			params['feedback'] = True

		# addressed
		try:
			message = self.addressed.search(message).group(1)
			params['addressed'] = True
		except: pass

		return message, params

	# returns our help data as a string
	def usage(self):
		return '\n'.join(self.usageLines)

	def processThread(self, **params):
		response = params['module'].response(**params)
		if response is not None:
			self.outputLock.acquire()
			self.output(message=response, params=params)
			self.outputLock.release()


	# actually process messages!
	def processMessage(self, message=None, params=None):
		if params.has_key('feedback') is True and params['feedback'] is True:
			self.output(message='yes?', params=params)
			return

		if params.has_key('addressed') is True and params['addressed'] is True:
			if message.lower() == 'help':
				self.output(message=self.usage(), params=params)
				return

		for module in self.modules.values():
			if module.requireAddressing is True:
				if params.has_key('addressed') is True and params['addressed'] is False:
					continue


			try: matchGroups = module.pattern.search(message).groups()
			except: continue

			kwargs = params
			kwargs['args'] = matchGroups
			kwargs['module'] = module

			if self.allowThreading is True and module.thread is True:
				t = threading.Thread(target=self.processThread, kwargs=kwargs)
				t.start()
			else:
				response = module.response(**kwargs)
				if response is not None: self.output(message=response, params=kwargs)


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
			isFloat = re.compile('^\d+\.\d+$')
			isTrue = re.compile('^\s*(true|yes|on|1)\s*$')
			isFalse = re.compile('^\s*(false|no|off|0)\s*$')

			for key, val in opts:
				if isInt.search(val): val = int(val)
				elif isFloat.search(val): val = float(val)
				elif isTrue.search(val): val = True
				elif isFalse.search(val): val = False
				setattr(self, key, val)

	def __getattr__(self, attr):
		try: return getattr(self, attr)
		except:
			try: return getattr(self, attr.lower())
			except: return None



"""
Standard method of daemonizing on POSIX systems
"""
def detach():
	if os.name != 'posix': return False
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
	return True


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

	# dynamic load of protocol handler
	try:
		module = __import__(protocol, globals(), locals(), ['ProtocolHandler'])
		ProtocolHandler = getattr(module, 'ProtocolHandler')
	except Exception, e:
		print >> sys.stderr, "FATAL: Couldn't load protocol %s: %s" % (protocol, e)
		return 1

	# daemonize if requested
	if config.main.detach is True or opts.detach is True:
		if detach() is True: opts.verbose = False

	bot = ProtocolHandler(config=config, dir=dir, verbose=opts.verbose)
	bot.start()

	return 0


if __name__ == '__main__': sys.exit(main())
