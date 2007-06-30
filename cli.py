#!/usr/bin/env python

from madcow import madcow
import os

class OutputHandler(madcow):
	def __init__(self, config):
		self.config = config
		self.allowThreading = False
		madcow.__init__(self)

	def start(self, *args):
		output = lambda m: self.output(m)
		while True:
			input = raw_input('>>> ').strip()

			if input.lower() == 'quit': break
			if len(input) > 0:
				self.processMessage(input, os.environ['USER'], 'cli', True, output)

	def output(self, message):
		print '%s' % message
