#!/usr/bin/env python

from madcow import Madcow, Request
import os
from include.colorlib import ColorLib

class ProtocolHandler(Madcow):
	def __init__(self, config=None, dir=None, verbose=False):
		self.allowThreading = False
		self.colorlib = ColorLib(type='ansi')
		Madcow.__init__(self, config=config, dir=dir, verbose=verbose)

	def start(self, *args):
		while True:
			input = raw_input('>>> ').strip()

			if input.lower() == 'quit': break
			if len(input) > 0:
				req = Request(message=input)
				req.nick = os.environ['USER']
				req.channel = 'cli'
				req.private = True
				req.addressed = True

				self.checkAddressing(req)

				if req.message.startswith('^'):
					req.colorize = True
					req.message = req.message[1:]

				self.processMessage(req)

	def output(self, message, req):
		if req.colorize is True:
			message = self.colorlib.rainbow(message)

		print message
