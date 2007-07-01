#!/usr/bin/env python

__version__ ='1.0.0'

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
import optparse
import os
import ConfigParser
import copy
import re
import threading
import time

class madcow(object):
	def __init__(self, config=None):
		if config is not None: self.config = config
		self.ns = self.config.modules.dbnamespace
		self.ignoreModules = [ '__init__', 'template' ]
		self.dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		self.moduleDir = self.dir + '/modules'
		self.verbose = True
		self.loadModules()
		self.outputLock = threading.RLock()

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
		self.usageLines = []

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


class Config(object):
	def __init__(self, configFile = None):
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.read(configFile)
		self.isInt = re.compile('^[0-9]+$')
		self.isFloat = re.compile('^[0-9.]+$')
		self.isTrue = re.compile('^\s*(true|yes|on|1)\s*$')
		self.isFalse = re.compile('^\s*(false|no|off|0)\s*$')
		self._module = None

	def __getattr__(self, arg):
		if arg.startswith('__'): return getattr(self, arg)
		if self._module is None:
			new = copy.deepcopy(self)
			new._module = arg
			return new
		else:
			val = self.cfg.get(self._module, arg)
			if self.isInt.search(val):
				return int(val)
			elif self.isFloat.search(val):
				return float(val)
			elif self.isTrue.search(val):
				return True
			elif self.isFalse.search(val):
				return False
			else:
				return val


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


def parseOptions():
	config = os.path.abspath(os.path.dirname(sys.argv[0])) + '/madcow.ini'
	parser = optparse.OptionParser(version=__version__)
	parser.add_option('-c', '--config', default=config, help='use FILE for config (default: %default)', metavar='FILE')
	parser.add_option('-d', '--detach', action='store_true', default=False, help='detach when run (default: %default)')
	opts, args = parser.parse_args()
	return opts


def main(argv = None):
	opts = parseOptions()
	config = Config(opts.config)

	if config.main.detach is True or opts.detach is True: detach()

	exec 'from %s import OutputHandler' % config.main.module
	bot = OutputHandler(config)
	bot.start()

	return 0

if __name__ == '__main__': sys.exit(main())
