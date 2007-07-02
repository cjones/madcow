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
				self.processMessage(input, os.environ['USER'], 'cli', True, output)

	def output(self, message):
		print '%s' % message
