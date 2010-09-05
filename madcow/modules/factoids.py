#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Emulate Perl InfoBot's factoid feature"""

from madcow.util import Module
import logging as log
import re
from re import I
import os
import random
import encoding

try:
    import dbm
except ImportError:
    import anydbm as dbm

__version__ = u'0.1'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = []

class Factoids(object):

    """
    This is a straight port of infobot.pl factoid handling.
    yes, this code is totally ridiculous, but it works pretty well. :P
    """

    # precompiled regex for do_question
    _qwords = u'what|where|who'
    _normalizations = (
        (r'^\S+\s*[:-]+\s*', u''),
        (r'^hey\s*[-,.: ]+\s*', u''),
        (r'whois', u'who is'),
        (r'where can i find', u'where is'),
        (r'\bhow about\b', u'where is'),
        (r'\bda\b', u'the'),
        (r'^([gj]ee+z*|boy|golly|gosh)\s*[-,. ]+\s*', u''),
        (r'^(well|and|but|or|yes)\s*[-,. ]+\s*', u''),
        (r'^(does\s+)?(any|ne)\s*(1|one|body)\s+know\s+', u''),
        (r'^[uh]+m*\s*[-,. ]+\s*', u''),
        (r'^o+[hk]+(a+y+)?\s*[-,. ]+\s*', u''),
        (r'^w(ow|hee+|o+ho+)+\s*[,. ]+\s*', u''),
        (r'^(still|well)\s*,\s*', u''),
        (r'^(stupid\s+)?question\s*[:-]+\s*', u''),
        (r'(?:^| )(%s)\s+(.*)\s+(is|are)(?: |$)' % _qwords, r' \1 \3 \2 '),
        (r'(?:^| )(%s)\s+(\S+)\s+(is|are)(?: |$)' % _qwords, r' \1 \3 \2 '),
        (r'be tellin\'?g?', r'tell'),
        (r" '?bout", r' about'),
        (r',? any(hoo?w?|ways?)', r' '),
        (r',?\s*(pretty )*please\??\s*$', r'?'),
        (r'th(e|at|is) (((m(o|u)th(a|er) ?)?fuck(in\'?g?)?|hell|heck|(god-?)?'
         r'damn?(ed)?) ?)+', r''),
        (r'\bw+t+f+\b', r'where'),
        (r'this (.*) thingy?', r' \1'),
        (r'this thingy? (called )?', r''),
        (r'ha(s|ve) (an?y?|some|ne) (idea|clue|guess|seen) ', r'know '),
        (r'does (any|ne|some) ?(1|one|body) know ', r''),
        (r'do you know ', r''),
        (r'can (you|u|((any|ne|some) ?(1|one|body)))( please)? tell (me|us|hi'
         r'm|her)', r''),
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
    _verbs = (u'is', u'are')
    _get_verb = re.compile(r'^.*?(is|are)\s+(?:(an?|the)\s+)?(.+)\s*$')
    _results = re.compile(r'\s*\|\s*')
    _isreply = re.compile(r'^\s*<reply>\s*', I)
    _reply_formats = (
        u'KEY is RESULT',
        u'i think KEY is RESULT',
        u'hmmm... KEY is RESULT',
        u'it has been said that KEY is RESULT',
        u'KEY is probably RESULT',
        u'rumour has it KEY is RESULT',
        u'i heard KEY was RESULT',
        u'somebody said KEY was RESULT',
        u'i guess KEY is RESULT',
        u'well, KEY is RESULT',
        u'KEY is, like, RESULT',
    )
    _unknown = (
        u"i don't know",
        u"i wish i knew",
        u"i haven't a clue",
        u"no idea",
        u"bugger all, i dunno",
    )
    _unknown_format = (
        u'NICK: RESULT',
        u'RESULT, NICK',
    )

    # precompiled regex for do_statement
    _normalize_statements = [
        (r'\bi am\b', u'NICK is', False),
        (r'\bmy\b', u"NICK's", False),
        (r'\byour\b', u"BOTNICK's", False),
        (r'\byou are\b', u'BOTNICK is', True),
        (r'^no\s*,\s*', u'', False),
        (r'^i\s+(heard|think)\s+', u'', False),
        (r'^some(one|1|body)\s+said\s+', u'', False),
        (r'\s+', u' ', False),
    ]
    _get_st_verb = re.compile(r'^(.*?)\b(is|are)\b(.*?)$', I)
    _article = re.compile(r'^(the|da|an?)\s+')
    _maxkey = 50
    _maxval = 325
    _st_qwords = u'who what where when why how'.split()
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

    def __init__(self, parent):
        self.parent = parent
        self.charset = self.parent.madcow.charset

    # DBM functions
    def get_dbm(self, dbname):
        dbfile = os.path.join(self.parent.madcow.base, 'db', dbname.lower())
        return dbm.open(dbfile, u'c', 0640)

    def get(self, dbname, key):
        dbm = self.get_dbm(dbname)
        try:
            key = key.lower().encode(self.charset, 'replace')
            val = dbm.get(key)
            if isinstance(val, str):
                val = val.decode(self.charset, 'replace')
            return val
        finally:
            dbm.close()

    def set(self, dbname, key, val):
        dbm = self.get_dbm(dbname)
        try:
            key = key.lower().encode(self.charset, 'replace')
            val = val.encode(self.charset, 'replace')
            dbm[key] = val
        finally:
            dbm.close()

    def unset(self, dbname, key):
        dbm = self.get_dbm(dbname)
        try:
            key = key.lower().encode(self.charset, 'replace')
            if dbm.has_key(key):
                del dbm[key]
                return True
            return False
        finally:
            dbm.close()

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
                    tell_obj = u' '.join([q, verb, tell_obj])
                except:
                    target = tell_obj = None
        if tell_obj:
            message = self._endpunc.sub(u'', tell_obj)

        if not target or target.lower() == u'me':
            target = nick
        elif target.lower() == u'us':
            target = None

        message, final_qmark = self._qmark.subn(u'', message)
        message = self._endpunc.sub(u'', message)

        # switchPerson from infobot.pl
        if target:
            who = target
        else:
            who = nick
        who = re.escape(who).lower()[:9].split()[0]
        botnick = self.parent.madcow.botname()

        # callback to interpolate the dynamic regexes
        interpolate = lambda x: x.replace(u'WHO', who).replace(
                u'BOTNICK', botnick).replace(u'NICK', nick)

        for norm, replacement, need_addressing in self._normalize_names:
            if need_addressing and not addressed:
                continue
            norm = interpolate(norm)
            replacement = interpolate(replacement)
            message = re.sub(norm, replacement, message)

        # this has to come after the punctuation check, i guess..
        message = self._whereat.sub(u'', message)

        # get qword
        message = message.strip()
        try:
            qword, message = self._qword.search(message).groups()
        except:
            qword = None
        if not qword and final_qmark and addressed:
            qword = u'where'

        # literal request?
        message, literal = self._literal.subn(u'', message)

        # if no verb specified, try both dbs for direct match?
        result = None
        for dbname in self._verbs:
            result = self.get(dbname, message)
            if result:
                verb = dbname
                key = message
                break

        # that didnu't work, let's try this..
        if not result and qword:
            try:
                verb, keymod, key = self._get_verb.search(message).groups()
                result = self.get(verb, key)
                if keymod:
                    key = u'%s %s' % (keymod, key)
            except:
                pass

        # output final result
        if result:
            if literal:
                return u'%s: %s =%s= %s' % (nick, key, verb, result)
            result = random.choice(self._results.split(result))
            result, short = self._isreply.subn(u'', result)
            if not short:
                if verb == u'is':
                    format = random.choice(self._reply_formats)
                    format = format.replace(u'KEY', key)
                    format = format.replace(u'RESULT', result)
                    result = format
                else:
                    result = u'%s %s %s' % (key, verb, result)
            result = result.replace(u'$who', nick)
            result = result.strip()

        # so.. should we really send it or not?
        if not final_qmark and not addressed and not tell_obj:
            result = None

        # did we actually figure this out? if not, say so only if explicit
        if qword or final_qmark:
            if addressed and not result:
                result = random.choice(self._unknown)
                format = random.choice(self._unknown_format)
                format = format.replace(u'RESULT', result)
                format = format.replace(u'NICK', nick)
                result = format

        # modify output parameters for tells
        if result and tell_obj:
            result = u'%s wants you to know: %s' % (nick, result)
            req.sendto = target

        return result

    def do_statement(self, message, nick, req):
        botnick = self.parent.madcow.botname()
        addressed = req.addressed
        private = req.private
        correction = req.correction

        # normalize
        message = message.strip()
        for norm, replacement, needs_addressing in self._normalize_statements:
            if needs_addressing and not addressed:
                continue
            replacement = replacement.replace(u'BOTNICK', botnick)
            replacement = replacement.replace(u'NICK', nick)
            message = re.compile(norm, I).sub(replacement, message)

        # does this look like a statement?
        try:
            key, verb, val = self._get_st_verb.search(message).groups()
        except:
            return

        # clean it up
        key = key.strip().lower()
        key = self._article.sub(u'', key)
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
        val, also = self._also.subn(u'', val)
        val, also_or = self._also_or.subn(u'', val)

        exists = self.get(verb, key)
        if exists == val:
            if addressed:
                return u'I already had it that way, %s' % nick
            else:
                return
        if exists:
            if also:
                if also_or:
                    val = exists + u'|' + val
                else:
                    val = exists + u' or ' + val
            elif not correction:
                if addressed:
                    return u'%s: but %s %s %s' % (nick, key, verb, exists)
                else:
                    return
        val = val[:self._maxval]
        self.set(verb, key, val)
        if addressed:
            return u'OK, %s' % nick

    def do_forget(self, message, nick, req):
        try:
            key, forget = self._forget.subn(u'', message)
        except:
            forget = 0
        if not forget:
            return
        key = self._endpunc.sub(u'', key).strip()

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
            return u'%s: I forgot %s' % (nick, key)
        else:
            return u"%s, I didn't find anything matching %s" % (nick, key)

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
            return u'%s: no entry in db for %s' % (nick, repr(key))

        if orig not in val:
            return u'%s: entry found, but %s is not in it' % (nick, repr(orig))

        val = val.replace(orig, new)
        self.set(dbname, key, val)
        return u'OK, %s' % nick


class Main(Module):
    pattern = Module._any
    require_addressing = False
    priority = 99
    allow_threading = False
    terminate = False

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.factoids = Factoids(parent=self)

    def response(self, nick, args, kwargs):
        try:
            result = self.factoids.parse(args[0], nick, kwargs[u'req'])
            return encoding.convert(result)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, self.error)


if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)

