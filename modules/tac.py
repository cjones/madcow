#!/usr/bin/env python

"""
$Id: tac.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Useful tool for oncall support!
"""

import sys
import re
import random

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('tac', re.I)	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'tac - handy tool if you do support'

		self.words = [
			[
				'Temporary', 'Intermittant', 'Partial', 'Redundant', 'Total',
				'Multiplexed', 'Inherent', 'Duplicated', 'Dual-Homed', 'Synchronous',
				'Bidirectional', 'Serial', 'Asynchronous', 'Multiple', 'Replicated',
				'Non-Replicated', 'Unregistered', 'Non-Specific', 'Generic',
				'Migrated', 'Localised', 'Resignalled', 'Dereferenced', 'Nullified',
				'Aborted', 'Serious', 'Minor', 'Major', 'Extraneous', 'Illegal',
				'Insufficient', 'Viral', 'Unsupported', 'Outmoded', 'Legacy',
				'Permanent', 'Invalid', 'Deprecated', 'Virtual', 'Unreportable',
				'Undetermined', 'Undiagnosable', 'Unfiltered', 'Static', 'Dynamic',
				'Delayed', 'Immediate', 'Nonfatal', 'Fatal', 'Non-Valid',
				'Unvalidated', 'Non-Static', 'Unreplicatable', 'Non-Serious',
			], [
				'temporary', 'intermittant', 'partial', 'redundant', 'total',
				'multiplexed', 'inherent', 'duplicated', 'dual-Homed', 'synchronous',
				'bidirectional', 'serial', 'asynchronous', 'multiple', 'replicated',
				'non-Replicated', 'unregistered', 'non-specific', 'generic',
				'migrated', 'localised', 'resignalled', 'dereferenced', 'nullified',
				'aborted', 'serious', 'minor', 'major', 'extraneous', 'illegal',
				'insufficient', 'viral', 'unsupported', 'outmoded', 'legacy',
				'permanent', 'invalid', 'deprecated', 'virtual', 'unreportable',
				'undetermined', 'undiagnosable', 'unfiltered', 'static', 'dynamic',
				'delayed', 'immediate', 'nonfatal', 'fatal', 'non-Valid',
				'unvalidated', 'non-static', 'unreplicatable', 'non-serious',
			], [
				'array', 'systems', 'hardware', 'software', 'firmware', 'backplane',
				'logic-subsystem', 'integrity', 'subsystem', 'memory', 'comms',
				'integrity', 'checksum', 'protocol', 'parity', 'bus', 'timing',
				'synchronisation', 'topology', 'transmission', 'reception', 'stack',
				'framing', 'code', 'programming', 'peripheral', 'environmental',
				'loading', 'operation', 'parameter', 'syntax', 'initialisation',
				'execution', 'resource', 'encryption', 'decryption', 'file',
				'precondition', 'authentication', 'paging', 'swapfile', 'service',
				'gateway', 'request', 'proxy', 'media', 'registry', 'configuration',
				'metadata', 'streaming', 'retrieval', 'installation', 'library',
				'handler',
			], [
				'interruption', 'destabilisation', 'destruction', 'desynchronisation',
				'failure', 'dereferencing', 'overflow', 'underflow', 'nmi',
				'interrupt', 'corruption', 'anomoly', 'seizure', 'override', 'reclock',
				'rejection', 'invalidation', 'halt', 'exhaustion', 'infection',
				'incompatibility', 'timeout', 'expiry', 'unavailability', 'bug',
				'condition', 'crash', 'dump', 'crashdump', 'stackdump', 'problem',
				'lockout', 'error', 'problem', 'warning', 'signal', 'flag',
			],
		]

	# function to generate a response
	def response(self, nick, args):
		try:
			problem = ' '.join([random.choice(set) for set in self.words])
			return '%s: %s' % (nick, problem)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: So broken I could't even come up with an excuse" % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
