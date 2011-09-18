"""Keep track of what people last said"""

import re
import time
import os
from madcow.util import Module
from madcow.util.textenc import *

try:
    import dbm
except ImportError:
    import anydbm as dbm

class Main(Module):

    pattern = Module._any
    priority = 1
    terminate = False
    allow_threading = False
    require_addressing = False
    help = u'seen <nick> - query bot about last time someone was seen speaking'
    seen = re.compile(u'^\s*seen\s+(\S+)\s*$', re.I)

    def init(self):
        self.dbfile = os.path.join(self.madcow.base, 'db', 'seen')

    def dbm(self):
        return dbm.open(self.dbfile, u'c', 0640)

    def get(self, user):
        db = self.dbm()
        try:
            user = encode(user.lower())
            packed = db[user]
            packed = decode(packed)
            channel, last, message = packed.split(u'/', 2)

            seconds = int(time.time() - float(last))
            last = u'%s second%s' % (seconds, u's' * (seconds != 1))

            minutes = seconds / 60
            seconds = seconds % 60
            if minutes:
                last = u'%s minute%s' % (minutes, u's' * (minutes != 1))

            hours = minutes / 60
            minutes = minutes % 60
            if hours:
                last = u'%s hour%s' % (hours, u's' * (hours != 1))

            days = hours / 24
            hours = hours % 24
            if days:
                last = u'%s day%s' % (days, u's' * (days != 1))

            return message, channel, last
        except:
            return None, None, None
        finally:
            db.close()

    def set(self, nick, channel, message):
        packed = u'%s/%s/%s' % (channel, time.time(), message)
        db = self.dbm()
        try:
            nick = encode(nick.lower())
            packed = encode(packed)
            db[nick] = packed
        finally:
            db.close()

    def response(self, nick, args, kwargs):
        channel = kwargs[u'channel']
        line = args[0]

        self.set(nick, channel, line)
        match = self.seen.search(line)
        if not match:
            return
        user = match.group(1)
        message, channel, last = self.get(user)
        if not message:
            return u"%s: I haven't seen %s say anything plz" % (nick, user)
        return u'%s: %s was last seen %s ago on %s saying "%s"' % (
                nick, user, last, channel, message)
