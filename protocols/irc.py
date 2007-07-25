#!/usr/bin/env python

import textwrap
from include import irclib
import time
import re
import sys
from madcow import Madcow, Request
from include.colorlib import ColorLib
import random
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL
import logging

# set for LOTS of verbosity
irclib.DEBUG = 0

class ProtocolHandler(Madcow):
	def __init__(self, config=None, dir=None):
		self.allowThreading = True
		self.colorlib = ColorLib(type='mirc')

		Madcow.__init__(self, config=config, dir=dir)

		if logging.root.level <= DEBUG:
			irclib.DEBUG = 1

		self.irc = irclib.IRC()
		self.server = self.irc.server()
		self.events = ['welcome', 'disconnect', 'kick', 'privmsg', 'pubmsg']
		self.channels = re.split('\s*[,;]\s*', self.config.irc.channels)

	def log(self, chan, nick, msg):
		line = '%s <%s> %s\n' % (time.strftime('%T'), nick, msg)
		file = '%s/logs/%s-irc-%s-%s' % (self.dir, self.ns, chan, time.strftime('%F'))

		try:
			fi = open(file, 'a')
			fi.write(line)
		finally:
			fi.close()

	def connect(self):
		self.status('[IRC] * Connecting to %s:%s' % (self.config.irc.host, self.config.irc.port), INFO)
		self.server.connect(self.config.irc.host, self.config.irc.port, self.config.irc.nick)

	def start(self):
		self.connect()
		for event in self.events:
			self.status('[IRC] * Registering event: %s' % event, INFO)
			self.server.add_global_handler(event, getattr(self, 'on_' + event), 0)

		self.irc.process_forever()

	def botName(self):
		return self.server.get_nickname()

	# welcome event triggers startup sequence
	def on_welcome(self, server, event):
		self.status('[IRC] * Connected', INFO)

		# TODO: identify with nickserv

		# become an oper
		if self.config.irc.oper is True:
			self.status('[IRC] * Becoming an OPER', INFO)
			self.server.oper(self.config.irc.operUser, self.config.irc.operPass)

		# join all channels
		for channel in self.channels:
			self.status('[IRC] * Joining: %s' % channel, INFO)
			self.server.join(channel)


	# when losing connection, reconnect if configured to do so, otherwise exit
	def on_disconnect(self, server, event):
		self.status('[IRC] * Disconnected from server', WARN)

		if self.config.irc.reconnect is True:
			if self.config.irc.reconnectWait > 0:
				time.sleep(self.config.irc.reconnectWait)
			self.connect()
		else:
			sys.exit(1)

	# when kicked, rejoin channel if configured to do so
	def on_kick(self, server, event):
		self.status('[IRC] * Kicked from %s by %s' % (event.arguments()[0], event.target()), WARN)
		if event.arguments()[0].lower() == server.get_nickname().lower():
			if self.config.irc.rejoin is True:
				if self.config.irc.rejoinWait > 0:
					time.sleep(self.config.irc.rejoinWait)
				server.join(event.target())
				server.privmsg(event.target(), self.config.irc.rejoinReply)

	# function to putput to IRC
	def output(self, message, req):
		if message is None: return

		if req.colorize is True:
			style = random.choice(ColorLib.rainbowStyles)
			message = self.colorlib.rainbow(message, style=style)

		if req.wrap is True:
			wrap = self.config.irc.wrap
		else:
			wrap = 400

		output = []
		for line in message.splitlines():
			for wrapped in textwrap.wrap(line, wrap):
				output.append(wrapped)

		for line in output:
			self.server.privmsg(req.sendTo, line)


	def on_privmsg(self, server, event):
		self.status('[IRC] PRIVMSG from %s: %s' % (event.source(), event.arguments()[0]), INFO)
		self.on_message(server, event, private=True)

	def on_pubmsg(self, server, event):
		self.status('[IRC] <%s/%s> %s' % (event.source(), event.target(), event.arguments()[0]), INFO)
		self.log(event.target(), irclib.nm_to_n(event.source()), event.arguments()[0])
		self.on_message(server, event, private=False)

	def on_message(self, server, event, private):
		req = Request(message=event.arguments()[0])
		req.nick = irclib.nm_to_n(event.source())
		req.channel = event.target()
		req.private = private

		if private is True:
			req.sendTo = req.nick
		else:
			req.sendTo = req.channel

		self.preProcess(req)
		self.processMessage(req)

	def preProcess(self, req):
		self.checkAddressing(req)

		if req.message.startswith('^'):
			req.message = req.message[1:]
			req.colorize = True
		else:
			req.colorize = False



