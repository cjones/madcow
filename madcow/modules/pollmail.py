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
    pattern = re.compile(r'^\s*pollmail\s+(.+?)\s*$')
    help = '\n'.join([
        'start - start automatic polling of email for messages',
        'stop - stop automatic polling of email for messages',
        'now - force one-time poll'
    ])
    error = u"I had an error"

    def init(self):
        try:
            self.madcow.imap_poller
        except AttributeError:
            self.madcow.imap_poller = ImapPoller(self.madcow)

        self.poller = self.madcow.imap_poller

    def response(self, nick, args, kwargs):
        command = args[0]

        if command == 'now':
            response = self.poller(True)

            if response == "":
                return "No new messages."
            else:
                return response

        if command == 'start':
            return self.poller.start(nick)

        if command == 'stop':
            return self.poller.stop(nick)