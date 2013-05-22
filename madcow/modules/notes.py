"""Allow staff to add notes to nicks"""

""" Copyright 2013 ActiveState Software Inc. """

import re
from madcow.util import Module
from madcow.util.text import *
from madcow.conf import settings
from learn import Main as Learn
from staff import Main as Staff
from datetime import datetime
import os

try:
    import dbm
except ImportError:
    import anydbm as dbm

class Main(Module):
    pattern = re.compile(u'^\s*(nb|notes?)(?:\s+(.*)$)?')
    require_addressing = True
    dbname = u'note'
    help = u'notes|nb <nick>                        show notes associated to a nick (staff only)\n\
notes|nb <nick> <note>                 add a note to a nick (staff only)'
    
    def init(self):
        self.learn = Learn(madcow=self.madcow)
        self.staff = Staff(madcow=self.madcow)
        
    def set(self, nick, target_nick, note):
        d = datetime.now()
        # append notes, don't overwrite
        old_notes = self.learn.lookup(self.dbname, target_nick) 
        notes = old_notes if old_notes else ""
        self.learn.set(self.dbname, target_nick.lower(), notes + '\n[' + d.strftime("%D") + '] [' + nick + '] ' + note)
        
    def get(self, target_nick):
        return self.learn.lookup(self.dbname, target_nick)
        
    def response(self, nick, args, kwargs):
        cmd = args[0]
        target_nick = False
        note = False
        params = []
        if args[1]:
            params = args[1].partition(' ')
        
        try:
            target_nick = params[0]
        except IndexError:
            target_nick = False
            
        try:
            note = params[2]
        except IndexError:
            note = False

        """ if nick passed, set user as staff """
        if target_nick and (self.staff.is_staff(nick) or settings.OWNER_NICK == nick):
            if note:
                self.set(nick=nick, target_nick=target_nick, note=note)
                return u'%s: Note added to %s\'s record.' % (nick, target_nick)
            else:
                notes = self.get(target_nick=target_nick)
                if notes:
                    return u'%s: Staff notes on %s\n%s' % (nick, target_nick, notes)
                else:
                    return u'%s: No notes found for %s' % (nick, target_nick)