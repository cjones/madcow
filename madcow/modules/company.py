"""Allow staff to get/set company information on nicks"""

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
    pattern = re.compile(u'^\s*(compan[y|ies])(?:\s+(.*)$)?')
    require_addressing = False
    dbname = u'company'
    help = u'companies                          list all company/nick associations (staff only)\n\
company <nick>                     show company associated with user (staff only)\n\
company <nick> <company_name>      set company information for user (staff only)'
    
    def init(self):
        self.learn = Learn(madcow=self.madcow)
        self.staff = Staff(madcow=self.madcow)
        
    def set(self, nick, company):
        self.learn.set(self.dbname, nick.lower(), company)
        
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
    
    def get_companies(self):
        company_db = self.learn.get_db('company');
        return company_db
    
    def has_company(self, nick):
        company_db = self.get_companies()
        return nick in company_db
   
    def get(self, nick):
        return self.learn.lookup(self.dbname, nick)
    
    def response(self, nick, args, kwargs):
        cmd = args[0]
        target_nick = False
        company = False
        params = []
        if args[1]:
            params = args[1].partition(' ')
        
        try:
            target_nick = params[0]
        except IndexError:
            target_nick = False
            
        try:
            company = params[2]
        except IndexError:
            company = False
            
        # only staff members & bot owner are allowed to get & set company data
        if self.staff.is_staff(nick) or settings.OWNER_NICK == nick:
            if target_nick:
                if company:
                    self.set(target_nick, company)
                    return u'%s: setting company for %s to %s' % ( nick, target_nick, company )
                else:
                    company_name = self.get(target_nick)
                    if company_name:
                        return u'%s: %s works at %s' % ( nick, target_nick, company_name )
                    else:
                        return u'%s: I don\'t know where %s works' % ( nick, target_nick )
            else:
                company_list = "\n\nRecorded companies:\n"
                for user_nick, company_name in self.get_companies().iteritems():
                    company_list = company_list + user_nick + " works at " + company_name + "\n"
                return u'%s: %s' % (nick, company_list)