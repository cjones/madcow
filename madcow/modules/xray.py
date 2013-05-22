"""Allow staff to get a summary of staff info on a nick"""

""" Copyright 2013 ActiveState Software Inc. """

import re
from madcow.util import Module
from madcow.util.text import *
from madcow.conf import settings
from learn import Main as Learn
from staff import Main as Staff
from company import Main as Company
from realname import Main as Realname
from notes import Main as Notes
import os

try:
    import dbm
except ImportError:
    import anydbm as dbm
    
class Main(Module):
    pattern = re.compile(u'^\s*(xray)(?:\s+(.*)$)?')
    require_addressing = False
    help = u'xray <nick>        show all staff-accessible data for <nick> (staff only)'
    
    def init(self):
        self.learn = Learn(madcow=self.madcow)
        self.staff = Staff(madcow=self.madcow)
        self.company = Company(madcow=self.madcow)
        self.realname = Realname(madcow=self.madcow)
        self.notes = Notes(madcow=self.madcow)
    
    def response(self, nick, args, kwargs):
        cmd = args[0]
        target_nick = args[1].strip()
        real_name = False
        
        # only staff members & bot owner are allowed to get xray data
        if self.staff.is_staff(nick) or settings.OWNER_NICK == nick:
            if target_nick:
                name = self.realname.get(target_nick);
                company = self.company.get(target_nick);
                notes = self.notes.get(target_nick);
                email = self.learn.lookup('email', target_nick)
                summary = ''
                if name:
                    summary = summary + 'Name: ' + name + '\n'
                if email:
                    summary = summary + 'Email: ' + email + '\n'
                if company:
                    summary = summary + 'Company: ' + company + '\n'
                if notes:
                    summary = summary + u'=' * 75 + notes + '\n'
                if summary:
                    return u'%s: Here\'s the skinny on %s\n\n%s' % (nick, target_nick, summary)
                else:
                    return u'%s: No data found for %s' % (nick, target_nick)
            else:
                return u'%s: xray only works if you tell me who to scan.' % (nick)