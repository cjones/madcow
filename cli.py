#!/usr/bin/env python

from madcow import Madcow
import os

class ProtocolHandler(Madcow):
	def __init__(self, config=None, dir=None, verbose=False):
		self.allowThreading = False
		Madcow.__init__(self, config=config, dir=dir, verbose=verbose)

	def start(self, *args):
		output = lambda m: self.output(m)
		while True:
			input = raw_input('>>> ').strip()

			if input.lower() == 'quit': break
			if len(input) > 0:
				params = dict([
					('nick', os.environ['USER']),
					('channel', 'cli'),
					('sendTo', os.environ['USER']),
					('private', True),
				])
				self.processMessage(message=input, params=params)

	def output(self, message=None, params=None):
		print '%s' % message
