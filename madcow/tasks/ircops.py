"""Periodically checks for people that need to be opped"""

from time import time as unix_time, sleep
from madcow.conf import settings
from madcow.util import Task

class Main(Task):

    def init(self):
        self.frequency = settings.UPDATER_FREQ
        self.output = None
        if settings.PROTOCOL != 'irc':
            raise ValueError('ircops only relevant for irc protocol')

    def response(self, *args):
        # determine who can be opped
        auto_op = []
        passwd = self.madcow.admin.authlib.get_passwd()
        for nick, data in passwd.items():
            if u'o' in data[u'flags']:
                auto_op.append(nick.lower())

        # issue NAMES update and wait for it to refresh (handled in irc.py)
        self.madcow.server.names(self.madcow.channels)
        while True:
            now = unix_time()
            delta = now - self.madcow.last_names_update
            if delta < self.frequency:
                break
            if delta >= (self.frequency * 2 -1):
                return
            sleep(.25)

        for channel, names in self.madcow.names.items():
            nicks = [nick for nick, opped in names.items() if not opped]
            if self.madcow.server.get_nickname() in nicks:
                self.log.warn(u'cannot give ops until i get it myself')
                return
            nicks = [nick for nick in nicks if nick in auto_op]
            for i in range(0, len(nicks), 6):
                line = nicks[i:i+6]
                self.log.info(u'opping on %s to %s' % (channel, u' '.join(line)))
                line = u'+' + (u'o' * len(line)) + u' ' + u' '.join(line)
                self.madcow.server.mode(channel, line)
