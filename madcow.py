#!/usr/bin/env python

"""
$Id:$
"""

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
import glob
import os
import ConfigParser
import copy
import re
import threading
from modules.include import factoids, seen, memebot

class madcow(object):
	def __init__(self):
		self.factoids = factoids.Factoids()
		self.seen = seen.Seen()
		self.memebot = memebot.MemeBot()
		self.ignoreModules = ['__init__', 'template', 'seen']
		self.moduleDir = os.path.abspath(os.path.dirname(sys.argv[0])) + '/modules'
		self.loadModules()
		self.outputLock = threading.RLock()

	def start(self):
		pass

	def output(self, message):
		pass

	def botName(self):
		pass

	# dynamically load module classes
	def loadModules(self):
		self.modules = {}
		self.usageLines = []
		for file in glob.glob(self.moduleDir + '/*.py'):
			moduleName = os.path.basename(file[0:-3])
			if moduleName in self.ignoreModules: continue
			module = __import__('modules.' + moduleName)
			exec 'obj = module.%s.match()' % moduleName
			if obj.enabled is False: continue
			self.modules[moduleName] = obj
			try:
				if obj.help: self.usageLines.append(obj.help)
			except:
				pass

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

	def processThread(self, obj, nick, args, output):
		response = obj.response(nick, args)
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

		# factoids
		response = self.factoids.check(nick, addressed, correction, message)
		if response is not None:
			output(response)

		# seen
		if private is False:
			response = self.seen.response(nick, channel, message)
			if response is not None:
				output(response)

		# memebot
		if private is False:
			response = self.memebot.check(nick, channel, message, addressed)
			if response is not None:
				output(response)


		### DYNAMIC MODULES ###

		for module, obj in self.modules.iteritems():
			if obj.requireAddressing and addressed is not True: continue

			try: args = obj.pattern.search(message).groups()
			except: continue

			if self.allowThreading is True and obj.thread is True:
				t = threading.Thread(target = self.processThread, args = (obj, nick, args, output))
				t.start()
			else:
				response = obj.response(nick, args)
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
