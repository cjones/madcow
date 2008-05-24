#!/usr/bin/env python

"""This implements the infobot factoid database work-a-like"""

import sys
import re
import anydbm
import random
from include.utils import Module

class Main(Module):
    pattern = Module._any
    require_addressing = False
    priority = 99
    qmark = re.compile('\s*\?+\s*$')
    isare = re.compile('^(.+?)\s+(is|are)\s+(.+)\s*$', re.I)
    query = re.compile('^(?:who|what|where|when|why|how|wtf)', re.I)
    ors   = re.compile('\s*\|\s*')
    reply = re.compile('^<reply>\s*(.+)', re.I)
    also  = re.compile('^\s*also\s+', re.I)
    isor  = re.compile('^\s*\|')
    forget = re.compile('forget[:\-, ]+(.+)$', re.I)

    def __init__(self, madcow=None):
        self.dir = madcow.dir
        self.ns = madcow.ns

    def dbFile(self, db_type):
        return self.dir + '/data/db-%s-factoids-%s' % (self.ns, db_type.lower())

    def dbm(self, db_type):
        db_file = self.dbFile(db_type)
        return anydbm.open(db_file, 'c', 0640)

    def get(self, db_type, key, val=None):
        db = self.dbm(db_type)

        try:
            key = key.lower()
            if db.has_key(key):
                val = db[key]
        finally:
            db.close()

        return val

    def set(self, db_type, key, val):
        db = self.dbm(db_type)
        db[key.lower()] = val
        db.close()
        return None

    def unset(self, key):
        forgot = 0
        for db_type in ['is', 'are']:
            db = self.dbm(db_type)
            if db.has_key(key.lower()):
                del db[key.lower()]
                forgot += 1
            db.close()

        if forgot == 0:
            return False
        else:
            return True

    def response(self, nick, args, **kwargs):
        reply = self.get_response(nick, args, **kwargs)

        # only terminate if we didn't have a response
        if reply is None or not len(reply):
            kwargs['req'].matched = False
        return reply

    def get_response(self, nick, args, **kwargs):
        addressed = kwargs['addressed']
        correction = kwargs['correction']
        message = args[0]

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
                key, db_type, val = isare.groups()

                # the ispart is actually a query
                if self.query.search(key):
                    key = val
                    val = None
                    question = True

            elif question is True:
                key = message
                db_type = 'is'
                question = True
            else:
                return

            ### QUERY
            if question is True:
                val_is = self.get('is', key)
                val_are = self.get('are', key)

                if val_is is None and val_are is None:
                    val = None
                elif val_is is not None and db_type == 'is':
                    val = val_is
                elif val_are is not None and db_type == 'are':
                    val = val_are
                elif val_is is not None:
                    val = val_is
                    db_type = 'is'
                elif val_are is not None:
                    val = val_are
                    db_type = 'are'

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
                        response = '%s %s %s' % (key, db_type, val)
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
                setVal = self.get(db_type, key)

                if ((setVal is not None) and (also is True)):
                    if self.isor.search(val):
                        val = '%s %s' % (setVal, val)
                    else:
                        val = '%s or %s' % (setVal, val)
                elif ((setVal is not None) and (correction is False)):
                    if addressed:
                        return '%s: But %s %s %s' % (nick, key, db_type, setVal)
                    else: return

                self.set(db_type, key, val)
                if addressed:
                    return 'OK, %s' % nick

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


