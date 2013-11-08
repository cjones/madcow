"""Poll email address"""

import re
import imaplib
import json as JSON
from madcow.util import Module
from madcow.conf import settings
from madcow.util.text import *
from madcow.util.imap import ImapPoller

# Todo:
# Find a way to crate a single Poller that it used by the PollTask and the MainModule

class Main(Module):
    pattern = re.compile(r'^\s*mail\s+(.+?)\s*$')
    help = '\n'.join(['start - start automatic polling of email for messages', 'stop - stop automatic polling of email for messages', 'now - force one-time poll'])
    error = u"I had an error"

    def init(self):
        try:
            self.madcow.poller
        except AttributeError:
            self.madcow.poller = ImapPoller(self.madcow)

    def response(self, nick, args, kwargs):
        if args[0] is "pollmail":
            command = args[1]

            if command is 'now':
                self.poller(True)
                return "All mail polled."

            if command is 'start':
                return self.poller.start(nick)

            if command is 'stop':
                return self.poller.stop(nick)