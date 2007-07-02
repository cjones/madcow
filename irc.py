#!/usr/bin/env python

import textwrap
import irclib
import time
import re
import sys
from madcow import Madcow

# set for LOTS of verbosity
irclib.DEBUG = 0

class ProtocolHandler(Madcow):
	def __init__(self, config=None, dir=None, verbose=False):
		self.allowThreading = True
		Madcow.__init__(self, config=config, dir=dir, verbose=verbose)

		self.irc = irclib.IRC()
		self.server = self.irc.server()
		self.events = ['welcome', 'disconnect', 'kick', 'privmsg', 'pubmsg']
		self.channels = re.split('\s*[,;]\s*', self.config.irc.channels)

	def connect(self):
		self.server.connect(self.config.irc.host, self.config.irc.port, self.config.irc.nick)

	def start(self):
		self.connect()
		for event in self.events:
			self.server.add_global_handler(event, getattr(self, 'on_' + event), 0)
		self.irc.process_forever()

	def botName(self):
		return self.server.get_nickname()

	# welcome event triggers startup sequence
	def on_welcome(self, server, event):
		# TODO: identify with nickserv

		# become an oper
		if self.config.irc.oper is True:
			self.server.oper(self.config.irc.operUser, self.config.irc.operPass)

		# join all channels
		for channel in self.channels:
			self.server.join(channel)


	# when losing connection, reconnect if configured to do so, otherwise exit
	def on_disconnect(self, server, event):
		if self.config.irc.reconnect is True:
			if self.config.irc.reconnectWait > 0:
				time.sleep(self.config.irc.reconnectWait)
			self.connect()
		else:
			sys.exit(1)

	# when kicked, rejoin channel if configured to do so
	def on_kick(self, server, event):
		if event.arguments()[0].lower() == server.get_nickname().lower():
			if self.config.irc.rejoin is True:
				if self.config.irc.rejoinWait > 0:
					time.sleep(self.config.irc.rejoinWait)
				server.join(event.target())
				server.privmsg(event.target(), self.config.irc.rejoinReply)

	# function to putput to IRC
	def output(self, sendTo, message, wrap = False):
		if message is None: return

		if wrap is True:
			lines = textwrap.wrap(message, self.config.irc.wrap)
		elif wrap is False:
			lines = []
			for line in message.splitlines():
				lines = lines + textwrap.wrap(line, 400)

		for line in lines:
			self.server.privmsg(sendTo, line)


	def on_privmsg(self, server, event):
		self.on_message(server, event, private = True)

	def on_pubmsg(self, server, event):
		self.on_message(server, event, private = False)

	def on_message(self, server, event, private):
		message = event.arguments()[0]
		nick = irclib.nm_to_n(event.source())
		sendTo = private == True and nick or event.target()
		output = lambda m: self.output(sendTo, m)
		self.processMessage(message, nick, event.target(), private, output)
