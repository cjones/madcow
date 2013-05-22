"""Allow staff to get/set a real name for nicks"""

""" Copyright 2013 ActiveState Software Inc. """

import re
from madcow.util import Module
from madcow.util.text import *
from madcow.conf import settings
from learn import Main as Learn
from staff import Main as Staff
import os

try:
    import dbm
except ImportError:
    import anydbm as dbm
    
class Main(Module):
    pattern = re.compile(u'^\s*(names?)(?:\s+(.*)$)?')
    require_addressing = False
    dbname = u'realname'
    help = u'names                          show list of associated nicks and names (staff only)\n\
name <nick>                    show real name associated with user (staff only)\n\
name <nick> <real_name>        set real name for user (staff only)'
    
    def init(self):
        self.learn = Learn(madcow=self.madcow)
        self.staff = Staff(madcow=self.madcow)
        
    def set(self, nick, name):
        self.learn.set(self.dbname, nick.lower(), name)
        
    def unset(self, nick):
        dbm = self.learn.dbm(self.dbname)
        try:
            key = encode(nick.lower())
            if dbm.has_key(nick):
                del dbm[nick]
                return True
            return False
        finally:
            dbm.close()
    
    def get_names(self):
        name_db = self.learn.get_db('realname');
        return name_db
    
    def has_name(self, nick):
        name_db = self.get_names()
        return nick in name_db
   
    def get(self, nick):
        return self.learn.lookup(self.dbname, nick)
    
    def response(self, nick, args, kwargs):
        cmd = args[0]
        target_nick = False
        real_name = False
        params = []
        if args[1]:
            params = args[1].partition(' ')
        
        try:
            target_nick = params[0]
        except IndexError:
            target_nick = False
            
        try:
            real_name = params[2]
        except IndexError:
            real_name = False
            
        # only staff members & bot owner are allowed to get & set real_name data
        if self.staff.is_staff(nick) or settings.OWNER_NICK == nick:
            if target_nick:
                if real_name:
                    self.set(target_nick, real_name)
                    return u'%s: Setting name for %s to %s' % ( nick, target_nick, real_name )
                else:
                    name = self.get(nick=target_nick)
                    if name:
                        return u'%s: %s is %s' % ( nick, target_nick, name )
                    else:
                        return u'%s: Sorry, I don\'t who %s is.' % ( nick, target_nick )
            else:
                name_list = "\n\nRecorded names:\n"
                for user_nick, name in self.get_names().iteritems():
                    name_list = name_list + user_nick + ": " + name + "\n"
                return u'%s: %s' % (nick, name_list)