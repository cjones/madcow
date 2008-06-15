#!/usr/bin/env python

"""Infobot style karma"""

from include.utils import Base, Module
import re
from learn import Main as Learn
import logging as log

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Karma', 'Main']

class KarmaResponse(Base):

    def __init__(self, reply, matched):
        self.reply = reply
        self.matched = matched


class Karma(Base):
    """Infobot style karma"""
    _adjust_pattern = re.compile(r'^\s*(.*?)[+-]([+-]+)\s*$')
    _query_pattern = re.compile(r'^\s*karma\s+(\S+)\s*\?*\s*$')
    _dbname = 'karma'

    def __init__(self, madcow):
        self.learn = Learn(madcow)

    def process(self, nick, input):
        kr = KarmaResponse(reply=None, matched=False)

        # see if someone is trying to adjust karma
        try:
            target, adjustment = Karma._adjust_pattern.search(input).groups()
            # don't let people adjust their own karma ;p
            if nick.lower() != target.lower():
                self.adjust(nick=target, adjustment=adjustment)
            kr.matched = True
        except:
            pass

        # detect a query for someone's karma
        try:
            target = Karma._query_pattern.search(input).group(1)
            karma = self.query(nick=target)
            kr.matched = True
            kr.reply = "%s: %s's karma is %s" % (nick, target, karma)
        except:
            pass

        return kr

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


class Main(Module):
    """This object is autoloaded by the bot"""
    pattern = Module._any
    require_addressing = False
    help = "<nick>[++/--] - adjust someone's karma"
    allow_threading = False

    def __init__(self, madcow=None):
        self.karma = Karma(madcow)

    def response(self, nick, args, kwargs):
        """This function should return a response to the query or None."""
        input = args[0]
        try:
            kr = self.karma.process(nick, input)
            kwargs['req'].matched = kr.matched
            return kr.reply
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: problem with command: %s' % (nick, e)

