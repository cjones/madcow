#!/usr/bin/env python

"""
Keep track of what people last said
"""

import sys
import re
import anydbm
import time
import os


class MatchObject(object):

    def __init__(self, dir='..', ns='madcow', config=None):
        self.enabled = True
        self.pattern = re.compile('^(.+)$')
        self.requireAddressing = False
        self.thread = False
        self.wrap = False
        self.help = 'seen <nick> - query bot about last time someone was seen speaking'

        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
        self.file = dir + '/data/db-%s-seen' % ns
        self.seen = re.compile('^\s*seen\s+(\S+)\s*$', re.I)

    def dbm(self):
        return anydbm.open(self.file, 'c', 0640)

    def get(self, user):
        user = user.lower()
        db = self.dbm()

        try:
            packed = db[user]
            db.close()
            channel, last, message = packed.split('/', 2)

            seconds = int(time.time() - float(last))
            last = '%s second%s' % (seconds, 's' * (seconds != 1))

            minutes = seconds / 60
            seconds = seconds % 60
            if minutes: last = '%s minute%s' % (minutes, 's' * (minutes != 1))

            hours = minutes / 60
            minutes = minutes % 60
            if hours: last = '%s hour%s' % (hours, 's' * (hours != 1))

            days = hours / 24
            hours = hours % 24
            if days: last = '%s day%s' % (days, 's' * (days != 1))

            return message, channel, last
        except Exception, e:
            return None, None, None

    def set(self, nick, channel, message):
        packed = '%s/%s/%s' % (channel, time.time(), message)
        db = self.dbm()
        db[nick.lower()] = packed
        db.close()

    def response(self, **kwargs):
        nick = kwargs['nick']
        channel = kwargs['channel']
        line = kwargs['args'][0]

        try:
            self.set(nick, channel, line)

            match = self.seen.search(line)
            if not match: return

            user = match.group(1)
            message, channel, last = self.get(user)
            if not message:
                return "%s: I haven't seen %s say anything plz" % (nick, user)

            return '%s: %s was last seen %s ago on %s saying "%s"' % (nick, user, last, channel, message)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])], channel='#test')
    sys.exit(0)
