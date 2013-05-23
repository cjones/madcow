"""Mark and display staff users"""

"""Only other users marked as staff + madcow's owner can add/remove a user as staff"""

""" Copyright 2013 ActiveState Software Inc. """

import re
from madcow.util import Module
from madcow.util.text import *
from madcow.conf import settings
from learn import Main as Learn
import os

try:
    import dbm
except ImportError:
    import anydbm as dbm

class Main(Module):
    pattern = re.compile(u'^\s*(staff)(?:\s+(.*)$)?')
    require_addressing = False
    dbname = u'staff'
    help = u'staff                          list staff members\n\
staff <nick>                   check if specific user is a staff member\n\
staff <nick> add/remove        add/remove user from staff list (staff only)'
    
    def init(self):
        self.learn = Learn(madcow=self.madcow)
        
    def set(self, nick):
        self.learn.set(self.dbname, nick.lower(), True)
        
    def unset(self, nick):
        dbm = self.learn.dbm(self.dbname)
        try:
            key = encode(nick.lower())
            if dbm.has_key(key):
                del dbm[key]
                return True
            return False
        finally:
            dbm.close()
        
    def get_staff(self):
        staff_db = self.learn.get_db('staff');
        return staff_db
    
    def is_staff(self, nick):
        staff_db = self.get_staff()
        return nick in staff_db
        
    def response(self, nick, args, kwargs):
        cmd = args[0]
        target_nick = False
        action = False
        params = []
        if args[1]:
            params = args[1].split()
        try:
            target_nick = params[0]
        except IndexError:
            target_nick = False
            
        try:
            action = params[1]
        except IndexError:
            action = False

        """ if nick passed, set user as staff """
        if target_nick:
            # if an action is passed, and requesting user is staff or owner, perform the action
            if action and (self.is_staff(nick) or settings.OWNER_NICK == nick):
                if action == 'remove':
                    self.unset(nick=target_nick)
                    return u'%s: %s is no longer marked as staff' % (nick, target_nick)
                elif action == "add":
                    self.set(nick=target_nick)
                    return u'%s: %s is now marked as staff' % (nick, target_nick)
                else:
                    return u'%s: I\'m not sure what you want me to do here. \'%s\' is not a valid staff action.' %(nick, action)
            
            # otherwise, respond with staff membership status for nick, ignoring the action
            if self.is_staff(target_nick):
                return u'%s: Yes, %s is a staff member' %(nick, target_nick)
            else:
                return u'%s: No, %s is not a staff member' %(nick, target_nick)
        else:
            staff_db = self.get_staff()
            staff_nicks = staff_db.keys()
            if len(staff_nicks):
                return u'%s: Staff members are: %s' % (nick, ", ".join(staff_nicks))
            else:
                return u'%s: There are currently no users marked as staff members.' % (nick)