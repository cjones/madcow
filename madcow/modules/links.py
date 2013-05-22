"""Provide shortcuts for commonly requested links"""

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
    pattern = re.compile(u'^\s*(link|shortcut)s?(?:\s+(.*)$)?')
    require_addressing = False
    dbname = u'links'
    help = u'shortcuts                         show list of resource shortcuts\n\
link <shortcut>                   show link for specified shortcut \n\
link <shortcut> <url>             set link for specified shortcut (staff only)\n\
link <shortcut> delete           remove link for specified shortcut (staff only)'
    
    def init(self):
        self.learn = Learn(madcow=self.madcow)
        self.staff = Staff(madcow=self.madcow)
        
    def set(self, shortcut, url):
        self.learn.set(self.dbname, shortcut.lower(), url)
        
    def unset(self, shortcut):
        dbm = self.learn.dbm(self.dbname)
        try:
            key = encode(shortcut.lower())
            if dbm.has_key(shortcut):
                del dbm[shortcut]
                return True
            return False
        finally:
            dbm.close()
    
    def get_shortcuts(self):
        link_db = self.learn.get_db(self.dbname);
        return link_db
    
    def has_name(self, shortcut):
        link_db = self.get_shortcuts()
        return shortcut in link_db
   
    def get(self, shortcut):
        return self.learn.lookup(self.dbname, shortcut)
    
    def response(self, nick, args, kwargs):
        cmd = args[0]
        shortcut = False
        link = False
        params = []
        if args[1]:
            params = args[1].partition(' ')
        
        try:
            shortcut = params[0]
        except IndexError:
            shortcut = False
            
        try:
            link = params[2]
        except IndexError:
            link = False
            
        # only staff members & bot owner are allowed to set/change shortcuts
        if shortcut and link and (self.staff.is_staff(nick) or settings.OWNER_NICK == nick):
            if link == "delete":
                self.unset(shortcut)
                return u'%s: Okay, I\'ve deleted the link for %s.  It used to be %s, and now it\'s nothing. How sad.' % ( nick, shortcut, link )
            else:
                self.set(shortcut, link)
                return u'%s: Okay, I\'ve set the link for %s to %s' % ( nick, shortcut, link )
        elif shortcut:
            link_url = self.get(shortcut)
            if link_url:
                return u'%s: %s - %s' % (nick, shortcut, link_url)
            else:
                return u'%s: Sorry, there is no \'%s\' shortcut.' % (nick, shortcut)
        else:
            kwargs['req'].make_private() # don't spam the channel with all the links.  there could be a lot of them.
            links = self.get_shortcuts()
            if len(links):
                link_list = "Here are all the current shortcuts:\n"
                for shortcut, url in links.iteritems():
                    link_list = link_list + shortcut + ": " + url + "\n"
                return u'%s' % (link_list)
            else:
                return u'Sorry, no shortcuts have been defined yet.'