"""Periodically checks for people that need to be opped"""

from include.utils import Base
from time import time as unix_time, sleep
import logging as log

class Main(Base):

    def __init__(self, madcow):
        self.madcow = madcow
        self.enabled = madcow.config.ircops.enabled
        self.frequency = madcow.config.ircops.updatefreq
        self.output = None
        if madcow.config.main.module != 'irc':
            self.enabled = False

    def process(self):
        # determine who can be opped
        auto_op = []
        passwd = self.madcow.admin.authlib.get_passwd()
        for nick, data in passwd.items():
            if 'o' in data['flags']:
                auto_op.append(nick)

        # issue NAMES update and wait for it to refresh (handled in irc.py)
        self.madcow.server.names(self.madcow.channels)
        while True:
            now = unix_time()
            delta = now - self.madcow.last_names_update
            if delta < self.frequency:
                break
            if delta >= (self.frequency * 2 -1):
                return

        for channel, names in self.madcow.names.items():
            nicks = [nick for nick, opped in names.items() if not opped]
            if self.madcow.server.get_nickname() in nicks:
                log.warn('cannot give ops until i get it myself')
                return
            nicks = [nick for nick in nicks if nick in auto_op]
            for i in range(0, len(nicks), 6):
                line = nicks[i:i+6]
                log.info('opping on %s to %s' % (channel, ' '.join(line)))
                line = '+' + ('o' * len(line)) + ' ' + ' '.join(line)
                self.madcow.server.mode(channel, line)


