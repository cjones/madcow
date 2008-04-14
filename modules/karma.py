#!/usr/bin/env python

"""Infobot style karma"""

from include.utils import Base
import sys
import re
import os
from learn import MatchObject as Learn

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Karma', 'MatchObject']

class Karma(Base):
    """Infobot style karma"""
    _adjust_pattern = re.compile(r'^\s*(.*?)[+-]([+-]+)\s*$')
    _query_pattern = re.compile(r'^\s*karma\s+(\S+)\s*\?*\s*$')
    _dbname = 'karma'

    def __init__(self, ns, dir):
        self.learn = Learn(ns=ns, dir=dir)

    def process(self, nick, input):
        # see if someone is trying to adjust karma
        try:
            target, adjustment = Karma._adjust_pattern.search(input).groups()
            # don't let people adjust their own karma ;p
            if nick.lower() != target.lower():
                self.adjust(nick=target, adjustment=adjustment)
        except:
            pass

        # detect a query for someone's karma
        try:
            target = Karma._query_pattern.search(input).group(1)
            karma = self.query(nick=target)
            return "%s: %s's karma is %s" % (nick, target, karma)
        except:
            pass

    def set(self, nick, karma):
        self.learn.set(Karma._dbname, nick.lower(), str(karma))

    def adjust(self, nick, adjustment):
        karma = self.query(nick)
        adjustment, size = adjustment[0], len(adjustment)
        exec('karma ' + adjustment + '= size')
        self.set(nick=nick, karma=karma)

    def query(self, nick):
        karma = self.learn.lookup(Karma._dbname, nick.lower())
        if karma is None:
            karma = 0
            self.set(nick=nick, karma=karma)
        return int(karma)


class MatchObject(object):
    """This object is autoloaded by the bot"""
    _anything_regex = re.compile(r'^(.+)$', re.DOTALL)

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.ns = ns
        self.dir = dir
        self.config = config
        self.enabled = True
        self.pattern = MatchObject._anything_regex
        self.requireAddressing = False
        self.thread = False
        self.wrap = False
        self.help = "<nick>[++/--] - adjust someone's karma"
        self.karma = Karma(ns, dir)

    def response(self, **kwargs):
        """This function should return a response to the query or None."""

        nick = kwargs['nick']
        input = kwargs['args'][0]

        try:
            return self.karma.process(nick, input)
        except Exception, e:
            return '%s: problem with command: %s' % (nick, e)


def main():
    mo = MatchObject()
    nick = os.environ['USER']
    args = [' '.join(sys.argv[1:])]
    print mo.response(nick=nick, args=args)

if __name__ == '__main__':
    sys.exit(main())
