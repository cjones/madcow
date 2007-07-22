#!/usr/bin/env python

from madcow import Madcow, Request
import os
import re
from twisted.protocols import oscar
from twisted.internet import protocol, reactor
from modules.include import utils
from modules.include.colorlib import ColorLib

class ProtocolHandler(Madcow):
	def __init__(self, config=None, dir=None, verbose=False):
		self.allowThreading = False
		self.colorlib = ColorLib(type='html')
		Madcow.__init__(self, config=config, dir=dir, verbose=verbose)
		self.newline = re.compile('[\r\n]+')

	def start(self):
		server = ('login.oscar.aol.com', 5190)
		p = protocol.ClientCreator(
			reactor, OSCARAuth, self.config.aim.username, self.config.aim.password, icq = 0
		)
		p.connectTCP(*server)
		p.protocolClass.BOSClass._ProtocolHandler = self
		reactor.run()

	def output(self, message=None, req=None):
		if self.colorize is True:
			message = self.colorlib.rainbow(message)

		message = self.newline.sub('<br>', message)
		req.aim.sendMessage(req.nick, message)

class OSCARConnection(oscar.BOSConnection):
	capabilities = [oscar.CAP_CHAT]
	def initDone(self):
		self.requestSelfInfo().addCallback(self.gotSelfInfo)
		self.requestSSI().addCallback(self.gotBuddyList)

	def gotSelfInfo(self, user):
		self.name = user.name

	def gotBuddyList(self, l):
		self.activateSSI()
		self.setProfile(self._ProtocolHandler.config.aim.profile)
		self.setIdleTime(0)
		self.clientReady()

	def receiveMessage(self, user, multiparts, flags):
		# XXX oh god.. so broken right now =/ i wonder if anyone uses this
		user = user.name
		message = utils.stripHTML(multiparts[0][0])
		bot = self._ProtocolHandler
		callback = lambda m: bot.output(self, user, m)
		bot.processMessage(message, user, 'AIM', True, callback)

class OSCARAuth(oscar.OscarAuthenticator):
	BOSClass = OSCARConnection

