#!/usr/bin/env python

"""
This implements the infobot factoid database work-a-like
"""

import sys
import re
import os
import anydbm
import random


class MatchObject(object):

    def __init__(self, dir=None, ns='madcow', config=None):
        self.enabled = True
        self.pattern = re.compile('^(.+)$')
        self.requireAddressing = False
        self.thread = False
        self.wrap = False

        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
        self.dir = dir
        self.ns = ns

        self.qmark = re.compile('\s*\?+\s*$')
        self.isare = re.compile('^(.+?)\s+(is|are)\s+(.+)\s*$', re.I)
        self.query = re.compile('^(?:who|what|where|when|why|how|wtf)', re.I)
        self.ors   = re.compile('\s*\|\s*')
        self.reply = re.compile('^<reply>\s*(.+)', re.I)
        self.also  = re.compile('^\s*also\s+', re.I)
        self.isor  = re.compile('^\s*\|')
        self.forget = re.compile('forget[:\-, ]+(.+)$', re.I)

    def dbFile(self, type):
        return self.dir + '/data/db-%s-factoids-%s' % (self.ns, type.lower())

    def get(self, type, key, val=None):
        db = anydbm.open(self.dbFile(type), 'c', 0640)

        try:
            key = key.lower()
            if db.has_key(key):
                val = db[key]
        finally:
            db.close()

        return val

    def set(self, type, key, val):
        db = anydbm.open(self.dbFile(type), 'c', 0640)
        db[key.lower()] = val
        db.close()
        return None

    def unset(self, key):
        forgot = 0
        for type in ['is', 'are']:
            db = anydbm.open(self.dbFile(type), 'c', 0640)
            if db.has_key(key.lower()):
                del db[key.lower()]
                forgot += 1
            db.close()

        if forgot == 0:
            return False
        else:
            return True

    def response(self, **kwargs):
        nick = kwargs['nick']
        addressed = kwargs['addressed']
        correction = kwargs['correction']
        message = kwargs['args'][0]

        try:
            # remove dubious whitespace
            message = message.strip()

            # see if we're trying to remove an entry
            forget = self.forget.search(message)
            if addressed is True and forget is not None:
                key = self.forget.sub('', forget.group(1))


                forgetResult = self.unset(key)

                if forgetResult is True:
                    return 'OK, %s' % nick
                else:
                    return '%s: nothing to forget..' % nick



            # strip off trailing qmark, which indicates a question, generally
            if self.qmark.search(message):
                message = self.qmark.sub('', message)
                question = True
            else:
                question = False


            # split up phrase by is/are seperator
            isare = self.isare.search(message)
            if isare is not None:
                key, type, val = isare.groups()

                # the ispart is actually a query
                if self.query.search(key):
                    key = val
                    val = None
                    question = True

            elif question is True:
                key = message
                type = 'is'
                question = True
            else:
                return

            ### QUERY
            if question is True:
                val_is = self.get('is', key)
                val_are = self.get('are', key)

                if val_is is None and val_are is None:
                    val = None
                elif val_is is not None and type == 'is':
                    val = val_is
                elif val_are is not None and type == 'are':
                    val = val_are
                elif val_is is not None:
                    val = val_is
                    type = 'is'
                elif val_are is not None:
                    val = val_are
                    type = 'are'

                if val is None:
                    if addressed is True:
                        return 'I have no idea, %s' % nick
                else:
                    # get a random selection from | delimited list
                    val = random.choice(self.ors.split(val))

                    # <reply> foo should just print 'foo'
                    reply = self.reply.search(val)
                    if reply is not None:
                        return reply.group(1)
                    else:
                        response = '%s %s %s' % (key, type, val)
                        if addressed:
                            response = '%s: %s' % (nick, response)
                        return response

            ### SET
            else:
                # see if we're trying to append
                if self.also.search(val):
                    val = self.also.sub('', val)
                    also = True
                else:
                    also = False

                # see if it's already set
                setVal = self.get(type, key)

                if ((setVal is not None) and (also is True)):
                    if self.isor.search(val):
                        val = '%s %s' % (setVal, val)
                    else:
                        val = '%s or %s' % (setVal, val)
                elif ((setVal is not None) and (correction is False)):
                    if addressed: return '%s: But %s %s %s' % (nick, key, type, setVal)
                    else: return

                self.set(type, key, val)
                if addressed: return 'OK, %s' % nick

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


if __name__ == '__main__':
    args = sys.argv[1:]
    a = args[0] == 'True' and True or False
    c = args[1] == 'True' and True or False
    print MatchObject().response(nick=os.environ['USER'], addressed=a, correction=c, args=[args[2]])
    sys.exit(0)
