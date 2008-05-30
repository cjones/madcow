#!/usr/bin/env python

"""Emulate Perl InfoBot's factoid feature"""

from include.utils import Module, Base
import logging as log
import re
from re import I
import os
import anydbm
import random

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008'
__all__ = []

class Factoids(Base):
    """
    This is a straight port of infobot.pl factoid handling.
    yes, this code is totally ridiculous, but it works pretty well. :P
    """

    # precompile as many regex as we can
    _qwords = '|'.join('what where who'.split())
    _talkingto = re.compile(r'^\s*\S+\s*[:-]+\s*')
    _mnorms = (
        (r'^\s*hey,*\s+where', 'where'),
        (r'whois', 'who is'),
        (r'where can i find', 'where is'),
        (r'how about', 'where is'),
        (r'\s+da\s+', ' the '),
        (r'^\s*(gee|boy|golly|gosh)\s*,?\s*', ''),
        (r'^(well|and|but|or|yes)\s*,?\s*', ''),
        (r'^\s*(does\s+)?(any|ne)\s*(1|one|body)\s+know\s+', ''),
        (r'^\s*heya?\s*,?\s*\S+\.\s+', ''),
        (r'^\s*[uh]+m*[,.]*\s+', ''),
        (r'^\s*o+[hk]+(a+y+)?[,.]*\s+', ''),
        (r'^\s*g(ee+z|osh|olly)+[,.]*\s+', ''),
        (r'^\s*w(ow|hee+|o+ho+)+[,.]*\s+', ''),
        (r'^\s*still\s*,\s*', ''),
        (r'^\s*well\s*,\s*', ''),
        (r'^\s*(stupid\s+)?question\s*[:-]+\s*', ''),
    )
    _mnorms = [(re.compile(x, I), y) for x, y in _mnorms]

    _tell = r'^\s*tell\s+(\S+)\s+'
    _tell1 = re.compile(_tell + r'about[: ]+(.+)', I)
    _tell2 = re.compile(_tell + r'where\s+(?:\S+)\s+can\s+(?:\S+)\s+(.+)', I)
    _tell3 = re.compile(_tell + r'(%s)\s+(.*?)\s+(is|are)[.?!]*$' % _qwords, I)

    _endpunc = re.compile(r'[.?!]+\s*$')
    _qmark = re.compile(r'[?!]*\?[?!1]*\s*$')

    _qnorms = [
        (r'(?:^| )(%s)\s+(.*)\s+(is|are)(?: |$)' % _qwords, r' \1 \3 \2 '),
        (r'(?:^| )(%s)\s+(\S+)\s+(is|are)(?: |$)' % _qwords, r' \1 \3 \2 '),
        (r'be tellin\'?g?', r'tell'),
        (r" '?bout", r' about'),
        (r',? any(hoo?w?|ways?)', r' '),
        (r',?\s*(pretty )*please\??\s*$', r'?'),
        (r'th(e|at|is) (((m(o|u)th(a|er) ?)?fuck(in\'?g?)?|hell|heck|(god-?)?damn?(ed)?) ?)+', r''),
        (r'wtf', r'where'),
        (r'this (.*) thingy?', r' \1'),
        (r'this thingy? (called )?', r''),
        (r'ha(s|ve) (an?y?|some|ne) (idea|clue|guess|seen) ', r'know '),
        (r'does (any|ne|some) ?(1|one|body) know ', r''),
        (r'do you know ', r''),
        (r'can (you|u|((any|ne|some) ?(1|one|body)))( please)? tell (me|us|him|her)', r''),
        (r'where (\S+) can \S+ (a|an|the)?', r''),
        (r'(can|do) (i|you|one|we|he|she) (find|get)( this)?', r'is'),
        (r'(i|one|we|he|she) can (find|get)', r'is'),
        (r'(the )?(address|url) (for|to) ', r''),
        (r'(where is )+', r'where is '),
    ]

    _qnorms = [(re.compile(x, I), y) for x, y in _qnorms]
    _whereat = re.compile(r'\s+at\s*(\?*)$', I)
    _contractions = re.compile(r"(?:^| )(%s)'?s(?: |$)" % _qwords, I)
    _qword = re.compile(r'(?:^|^(.*?)\s+)(%s)(?:$|\s+(.*)$)' % _qwords, I)
    _literal = re.compile(r'^\s*literal\s+', I)
    _verbs = ('is', 'are')
    _ydets = re.compile(r'^\s*(an?|the)\s+(.*?)$')
    _results = re.compile(r'\s*\|\s*')
    _isreply = re.compile(r'^\s*<reply>\s*', I)
    _reply_formats = (
        'KEY is RESULT',
        'i think KEY is RESULT',
        'hmmm... KEY is RESULT',
        'it has been said that KEY is RESULT',
        'KEY is probably RESULT',
        'rumour has it KEY is RESULT',
        'i heard KEY was RESULT',
        'somebody said KEY was RESULT',
        'i guess KEY is RESULT',
        'well, KEY is RESULT',
        'KEY is, like, RESULT',
    )

    # DBM functions
    def get_dbm(self, dbname):
        dbfile = 'db-%s-%s' % (self.parent.madcow.ns, dbname.lower())
        dbfile = os.path.join(self.parent.madcow.dir, 'data', dbfile)
        return anydbm.open(dbfile, 'c', 0640)

    def get(self, dbname, key):
        dbm = self.get_dbm(dbname)
        val = dbm.get(key)
        dbm.close()
        return val

    def set(self, dbname, key, val):
        dbm = self.get_dbm(dbname)
        dbm[key] = val
        dbm.close()

    def unset(self, dbname, key):
        dbm = self.get_dbm(dbname)
        forgot = False
        try:
            del dbm[key]
            forgot = True
        finally:
            dbm.close()
        return forgot

    def parse(self, message, nick, req):
        addressed = req.addressed
        correction = req.correction

        # message normalizations
        message = message.strip()
        message = self._talkingto.sub('', message)
        for norm, replacement in self._mnorms:
            message = norm.sub(replacement, message)

        # parse syntax for instructing bot to speak to someone else
        try:
            target, key = self._tell1.search(message).groups()
        except:
            try:
                target, key = self._tell2.search(message).groups()
            except:
                try:
                    target, q, key, verb = self._tell3.search(message).groups()
                    key = ' '.join([q, verb, key])
                except Exception, e:
                    target = key = None
        if key:
            message = self._endpunc.sub('', key)

        if not target or target.lower() == 'me':
            target = nick
        elif target.lower() == 'us':
            target = None

        # parse for question
        message = message.strip()
        final_qmark = False
        if self._qmark.search(message):
            message = self._qmark.sub('', message)
            final_qmark = True

        # query normalizations
        for norm, replacement in self._qnorms:
            message = norm.sub(replacement, message)
        message = message.strip()
        if self._qmark.search(message):
            message = self._qmark.sub('', message)
            final_qmark = True

        # switchPerson from infobot.pl
        if target:
            who = target
        else:
            who = nick
        who = re.escape(who).lower()[:9].split()[0]
        botnick = self.parent.madcow.botName()

        # even more normalizations based on nicks
        message = re.compile(r'(^|\W)%ss\s+' % who, I).sub(r'\1%s\'s '% nick,
                message)
        message = re.compile(r'(^|\W)%ss$' % who, I).sub(r'\1%s\'s' % nick,
                message)
        message = re.compile(r'(^|\W)%s\'(\s|$)' % who,
                I).sub(r'\1%s\'s\2' % nick, message)
        message = re.compile(r'(^|\s)i\'m(\W|$)', I).sub(r'\1%s is\2' % nick,
                message)
        message = re.compile(r'(^|\s)i\'ve(\W|$)', I).sub(r'\1%s has\2' % nick,
                message)
        message = re.compile(r'(^|\s)i have(\W|$)', I).sub(r'\1%s has\2' % nick,
                message)
        message = re.compile(r'(^|\s)i haven\'?t(\W|$)',
                I).sub(r'\1%s has not\2' % nick, message)
        message = re.compile(r'(^|\s)i(\W|$)', I).sub(r'\1%s\2' % nick, message)
        message = re.compile(r' am\b', I).sub(r' is', message)
        message = re.compile(r'\bam ', I).sub(r'is', message)
        if addressed:
            message = re.compile(r'yourself', I).sub(botnick, message)
        message = re.compile(r'(^|\s)(me|myself)(\W|$)',
                I).sub(r'\1%s$3' % nick, message)
        message = re.compile(r'(^|\s)my(\W|$)', I).sub(r'\1%s\'s\2' % nick,
                message)
        message = re.compile(r'(^|\W)you\'?re(\W|$)', I).sub(r'\1you are\2',
                message)
        if addressed:
            message = re.compile(r'(^|\W)are you(\W|$)',
                    I).sub(r'\1is %s\2' % botnick, message)
            message = re.compile(r'(^|\W)you are(\W|$)',
                    I).sub(r'\1%s is\2' % botnick, message)
            message = re.compile(r'(^|\W)you(\W|$)', I).sub(r'\1%s\2' % botnick,
                    message)
            message = re.compile(r'(^|\W)your(\W|$)',
                    I).sub(r'\1%s\'s\2' % botnick, message)

        # a couple more normalizations.. can go elsewhere?
        message = self._whereat.sub(r'\1', message)
        message = self._contractions.sub(r' \1 is ', message)

        # get qword
        # XXX this is flawed even in infobot.. is it trying too hard?
        # e.g.: your mom is what i'm sayin -> your mom isi'm sayin
        # ... what are they trying to accomplish here??
        try:
            before, qword, after = self._qword.search(message).groups()
            if not before:
                before = ''
            if not after:
                after = ''
            message = before + after
        except:
            qword = None
        message = message.strip()
        if not qword and final_qmark and addressed:
            qword = 'where'
        
        # infobot: getReply
        # XXX this is totally shit.. 
        # XXX its getting lowered before even here, but orig_y is useless w/o
        message = message.lower()
        message, literal = self._literal.subn('', message)
        v = y = orig_y = None
        ydet = ''
        for verb in self._verbs:
            result = self.get(verb, message)
            if result:
                # XXX is this really necessary :/
                v = verb
                y = result
                orig_y = message
                break
        if not v: # D:
            l = message.split()
            for verb in self._verbs:
                if verb in l:
                    i = l.index(verb)
                    y = l[i:]
                    v = y.pop(0)
                    y = ' '.join(y)
                    orig_y = y
                    y = y.lower()
                    try:
                        ydet, y = self._ydets.search(y).groups()
                    except:
                        ydet = ''
                    if qword:
                        if v == 'is':
                            result = self.get('is', y)
                        elif v == 'are':
                            result = self.get('are', y)

                    the_verb = v
                    break
        if not v:
            try:
                ydet, message = self._ydets.search(message).groups()
            except:
                ydet = ''
            message = self._endpunc.sub('', message)
            check = self.get('is', message)
            if check:
                result = check
                orig_y = message
                v = 'is'
            else:
                check = self.get('are', message)
                if check:
                    result = check
                    v = 'are'
                    orig_y = message
            if ydet:
                orig_y = '%s %s' % (ydet, orig_y)

        if not literal:
            result = random.choice(self._results.split(result))

        if result:
            if literal:
                return '%s: %s =%s= %s' % (nick, orig_y, v, result)
            result, short = self._isreply.subn('', result)
            if not short:
                if v == 'is':
                    format = random.choice(self._reply_formats)
                    format = format.replace('KEY', orig_y)
                    format = format.replace('RESULT', result)
                    result = format
                else:
                    result = '%s %s %s' % (orig_y, v, result)

        """
        # XXX this seems horribly flawed.........
        # XXX fix outgoing name purification
        if not short:
            result = re.sub(r'%s is' % who, 'you are', result)
            result = re.sub(r'%s is' % botnick, 'i am', result)
            result = re.sub(r'%s was' % botnick, 'i was', result)
            if addressed:
                result = re.sub(r'you are', 'i am') # XXX ?? wtf
        """


        # some stuff people can insert into the reply
        result = result.replace('$who', nick)
        result = result.strip()
        return result


class Main(Module):
    pattern = Module._any
    require_addressing = False
    priority = 99
    allow_threading = False

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.factoids = Factoids(parent=self)

    def response(self, nick, args, **kwargs):
        try:
            return self.factoids.parse(args[0], nick, kwargs['req'])
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)

