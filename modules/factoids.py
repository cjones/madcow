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

    # precompiled regex for do_question
    _qwords = 'what|where|who'
    _normalizations = (
        (r'^\S+\s*[:-]+\s*', ''),
        (r'^hey\s*[-,.: ]+\s*', ''),
        (r'whois', 'who is'),
        (r'where can i find', 'where is'),
        (r'\bhow about\b', 'where is'),
        (r'\bda\b', 'the'),
        (r'^([gj]ee+z*|boy|golly|gosh)\s*[-,. ]+\s*', ''),
        (r'^(well|and|but|or|yes)\s*[-,. ]+\s*', ''),
        (r'^(does\s+)?(any|ne)\s*(1|one|body)\s+know\s+', ''),
        (r'^[uh]+m*\s*[-,. ]+\s*', ''),
        (r'^o+[hk]+(a+y+)?\s*[-,. ]+\s*', ''),
        (r'^w(ow|hee+|o+ho+)+\s*[,. ]+\s*', ''),
        (r'^(still|well)\s*,\s*', ''),
        (r'^(stupid\s+)?question\s*[:-]+\s*', ''),
        (r'(?:^| )(%s)\s+(.*)\s+(is|are)(?: |$)' % _qwords, r' \1 \3 \2 '),
        (r'(?:^| )(%s)\s+(\S+)\s+(is|are)(?: |$)' % _qwords, r' \1 \3 \2 '),
        (r'be tellin\'?g?', r'tell'),
        (r" '?bout", r' about'),
        (r',? any(hoo?w?|ways?)', r' '),
        (r',?\s*(pretty )*please\??\s*$', r'?'),
        (r'th(e|at|is) (((m(o|u)th(a|er) ?)?fuck(in\'?g?)?|hell|heck|(god-?)?damn?(ed)?) ?)+', r''),
        (r'\bw+t+f+\b', r'where'),
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
        (r"(?:^| )(%s)'?s(?: |$)" % _qwords, r' \1 is '),
    )
    _normalizations = [(re.compile(x, I), y) for x, y in _normalizations]
    _tell = r'^tell\s+(\S+)\s+'
    _tell1 = re.compile(_tell + r'about[: ]+(.+)', I)
    _tell2 = re.compile(_tell + r'where\s+(?:\S+)\s+can\s+(?:\S+)\s+(.+)', I)
    _tell3 = re.compile(_tell + r'(%s)\s+(.*?)\s+(is|are)[.?!]*$' % _qwords, I)
    _qmark = re.compile(r'\s*[?!]*\?[?!1]*\s*$')
    _endpunc = re.compile(r'\s*[.?!]+\s*$')
    _normalize_names = [
        (r'(^|\W)WHOs\s+', r"\1NICK's ", False),
        (r'(^|\W)WHOs$', r"\1NICK's", False),
        (r"(^|\W)WHO'(\s|$)", r"\1NICK's\2", False),
        (r"(^|\s)i'm(\W|$)", r'\1NICK is\2', False),
        (r"(^|\s)i've(\W|$)", r'\1NICK has\2', False),
        (r'(^|\s)i have(\W|$)', r'\1NICK has\2', False),
        (r"(^|\s)i haven'?t(\W|$)", r'\1NICK has not\2', False),
        (r'(^|\s)i(\W|$)', r'\1NICK\2', False),
        (r' am\b', r' is', False),
        (r'\bam ', r'is', False),
        (r'yourself', r'BOTNICK', True),
        (r'(^|\s)(me|myself)(\W|$)', r'\1NICK\3', False),
        (r'(^|\s)my(\W|$)', r'\1NICK\'s\2', False),
        (r"(^|\W)you'?re(\W|$)", r'\1you are\2', False),

        (r'(^|\W)are you(\W|$)', r'\1is BOTNICK\2', True),
        (r'(^|\W)you are(\W|$)', r'\1BOTNICK is\2', True),
        (r'(^|\W)you(\W|$)', r'\1BOTNICK\2', True),
        (r'(^|\W)your(\W|$)', r"\1BOTNICK's\2", True),
    ]
    _whereat = re.compile(r'\s+at$', I)
    _qword = re.compile(r'^(?:(%s)\s+)?(.+)$' % _qwords)
    _literal = re.compile(r'^\s*literal\s+', I)
    _verbs = ('is', 'are')
    _get_verb = re.compile(r'^.*?(is|are)\s+(?:(an?|the)\s+)?(.+)\s*$')
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
    _unknown = (
        "i don't know",
        "i wish i knew",
        "i haven't a clue",
        "no idea",
        "bugger all, i dunno",
    )
    _unknown_format = (
        'NICK: RESULT',
        'RESULT, NICK',
    )

    # precompiled regex for do_statement
    _normalize_statements = [
        (r'\bi am\b', 'NICK is', False),
        (r'\bmy\b', "NICK's", False),
        (r'\byour\b', "BOTNICK's", False),
        (r'\byou are\b', 'BOTNICK is', True),
        (r'^no\s*,\s*', '', False),
        (r'^i\s+(heard|think)\s+', '', False),
        (r'^some(one|1|body)\s+said\s+', '', False),
        (r'\s+', ' ', False),
    ]
    _get_st_verb = re.compile(r'^(.*?)\b(is|are)\b(.*?)$', I)
    _article = re.compile(r'^(the|da|an?)\s+')
    _maxkey = 50
    _maxval = 325
    _st_qwords = 'who what where when why how'.split()
    _st_fails = [
        re.compile(r'^(who|what|when|where|why|how|it) '),
        re.compile(r'^(this|that|these|those|they|you) '),
        re.compile(r'^(every(one|body)|we) '),
        re.compile(r'^\s*\*'),
        re.compile(r'^\s*<+[-=]+'),
        re.compile(r'^[\[<\(]\w+[\]>\)]'),
        re.compile(r'^heya?,? '),
        re.compile(r'^\s*th(is|at|ere|ese|ose|ey)'),
        re.compile(r'^\s*it\'?s?\W'),
        re.compile(r'^\s*if '),
        re.compile(r'^\s*how\W'),
        re.compile(r'^\s*why\W'),
        re.compile(r'^\s*h(is|er) '),
        re.compile(r'^\s*\D[\d\w]*\.{2,}'),
        re.compile(r'^\s*so is'),
        re.compile(r'^\s*s+o+r+[ye]+\b'),
        re.compile(r'^\s*supposedly'),
        re.compile(r'^all '),
    ]
    _also_or = re.compile(r'\s*\|\s*')
    _also = re.compile(r'^also\s+')
    _forget = re.compile(r'^forget\s+((an?|the)\s+)?', I)
    _replace = re.compile(r'^\s*(.+?)\s*=~\s*s/(.+?)/(.*?)/\s*$')

    # DBM functions
    def get_dbm(self, dbname):
        dbfile = 'db-%s-%s' % (self.parent.madcow.ns, dbname.lower())
        dbfile = os.path.join(self.parent.madcow.dir, 'data', dbfile)
        return anydbm.open(dbfile, 'c', 0640)

    def get(self, dbname, key):
        dbm = self.get_dbm(dbname)
        val = dbm.get(key.lower())
        dbm.close()
        return val

    def set(self, dbname, key, val):
        dbm = self.get_dbm(dbname)
        dbm[key.lower()] = val
        dbm.close()

    def unset(self, dbname, key):
        dbm = self.get_dbm(dbname)
        forgot = False
        try:
            del dbm[key.lower()]
            forgot = True
        finally:
            dbm.close()
        return forgot

    def parse(self, message, nick, req):
        for func in (self.do_replace, self.do_forget, self.do_question,
                self.do_statement):
            result = func(message, nick, req)
            if result:
                return result

    def do_question(self, message, nick, req):
        addressed = req.addressed

        # message normalizations
        message = message.strip()
        for norm, replacement in self._normalizations:
            message = norm.sub(replacement, message)

        # parse syntax for instructing bot to speak to someone else
        try:
            target, tell_obj = self._tell1.search(message).groups()
        except:
            try:
                target, tell_obj = self._tell2.search(message).groups()
            except:
                try:
                    target, q, tell_obj, verb = \
                        self._tell3.search(message).groups()
                    tell_obj = ' '.join([q, verb, tell_obj])
                except:
                    target = tell_obj = None
        if tell_obj:
            message = self._endpunc.sub('', tell_obj)

        if not target or target.lower() == 'me':
            target = nick
        elif target.lower() == 'us':
            target = None

        message, final_qmark = self._qmark.subn('', message)
        message = self._endpunc.sub('', message)

        # switchPerson from infobot.pl
        if target:
            who = target
        else:
            who = nick
        who = re.escape(who).lower()[:9].split()[0]
        botnick = self.parent.madcow.botName()

        # callback to interpolate the dynamic regexes
        interpolate = lambda x: x.replace('WHO', who).replace('BOTNICK',
                botnick).replace('NICK', nick)

        for norm, replacement, need_addressing in self._normalize_names:
            if need_addressing and not addressed:
                continue
            norm = interpolate(norm)
            replacement = interpolate(replacement)
            message = re.sub(norm, replacement, message)

        # this has to come after the punctuation check, i guess..
        message = self._whereat.sub('', message)

        # get qword
        message = message.strip()
        try:
            qword, message = self._qword.search(message).groups()
        except:
            qword = None
        if not qword and final_qmark and addressed:
            qword = 'where'

        # literal request?
        message, literal = self._literal.subn('', message)

        # if no verb specified, try both dbs for direct match?
        result = None
        for dbname in self._verbs:
            result = self.get(dbname, message)
            if result:
                verb = dbname
                key = message
                break

        # that didn't work, let's try this..
        if not result and qword:
            try:
                verb, keymod, key = self._get_verb.search(message).groups()
                result = self.get(verb, key)
                if keymod:
                    key = '%s %s' % (keymod, key)
            except:
                pass

        # output final result
        if result:
            if literal:
                return '%s: %s =%s= %s' % (nick, key, verb, result)
            result = random.choice(self._results.split(result))
            result, short = self._isreply.subn('', result)
            if not short:
                if verb == 'is':
                    format = random.choice(self._reply_formats)
                    format = format.replace('KEY', key)
                    format = format.replace('RESULT', result)
                    result = format
                else:
                    result = '%s %s %s' % (key, verb, result)
            result = result.replace('$who', nick)
            result = result.strip()

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

        # so.. should we really send it or not?
        if not final_qmark and not addressed and not tell_obj:
            result = None

        # did we actually figure this out? if not, say so only if explicit
        if qword or final_qmark:
            if addressed and not result:
                result = random.choice(self._unknown)
                format = random.choice(self._unknown_format)
                format = format.replace('RESULT', result)
                format = format.replace('NICK', nick)
                result = format

        # modify output parameters for tells
        if result and tell_obj:
            result = '%s wants you to know: %s' % (nick, result)
            req.sendTo = target

        return result

    def do_statement(self, message, nick, req):
        botnick = self.parent.madcow.botName()
        addressed = req.addressed
        private = req.private
        correction = req.correction

        # normalize
        message = message.strip()
        for norm, replacement, needs_addressing in self._normalize_statements:
            if needs_addressing and not addressed:
                continue
            replacement = replacement.replace('BOTNICK', botnick)
            replacement = replacement.replace('NICK', nick)
            message = re.compile(norm, I).sub(replacement, message)

        # does this look like a statement?
        try:
            key, verb, val = self._get_st_verb.search(message).groups()
        except:
            return

        # clean it up
        key = key.strip().lower()
        key = self._article.sub('', key)
        key = key[:self._maxkey]
        val = val.strip()
        val = val[:self._maxval]

        # stuff to ignore to prevent storing dumb stuff
        if key in self._st_qwords:
            return
        if not addressed:
            try:
                for regex in self._st_fails:
                    if regex.search(key):
                        raise Exception
            except:
                return

        if not len(key):
            return

        # update db
        val, also = self._also.subn('', val)
        val, also_or = self._also_or.subn('', val)

        exists = self.get(verb, key)
        if exists == val:
            return 'I already had it that way, %s' % nick
        if exists:
            if also:
                if also_or:
                    val = exists + '|' + val
                else:
                    val = exists + ' or ' + val
            elif not correction:
                return '%s: but %s %s %s' % (nick, key, verb, exists)
        val = val[:self._maxval]
        self.set(verb, key, val)
        if addressed:
            return 'OK, %s' % nick

    def do_forget(self, message, nick, req):
        try:
            key, forget = self._forget.subn('', message)
        except:
            forget = 0
        if not forget:
            return
        key = self._endpunc.sub('', key).strip()

        # message normalizations
        for norm, replacement in self._normalizations:
            key = norm.sub(replacement, key)

        # remove
        found = False
        for dbname in self._verbs:
            if self.get(dbname, key):
                self.unset(dbname, key)
                found = True

        # respond
        if found:
            return '%s: I forgot %s' % (nick, key)
        else:
            return "%s, I didn't find anything matching %s" % (nick, key)

    def do_replace(self, message, nick, req):
        try:
            key, orig, new = self._replace.search(message).groups()
        except:
            return

        found = None
        for dbname in self._verbs:
            val = self.get(dbname, key)
            if val:
                found = val
                break
        if not found:
            return '%s: no entry in db for %s' % (nick, repr(key))

        if orig not in val:
            return '%s: entry found, but %s is not in it' % (nick, repr(orig))

        val = val.replace(orig, new)
        self.set(dbname, key, val)
        return 'OK, %s' % nick


class Main(Module):
    pattern = Module._any
    require_addressing = False
    priority = 99
    allow_threading = False
    terminate = False

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

