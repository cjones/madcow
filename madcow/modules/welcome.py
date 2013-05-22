"""Send/receive a welcome message"""

""" Copyright 2013 ActiveState Software Inc. """

import re
from madcow.util import Module
from madcow.util.text import *
from madcow.conf import settings
from staff import Main as Staff
import os

try:
    import dbm
except ImportError:
    import anydbm as dbm
    
class Main(Module):
    pattern = re.compile(u'^\s*(welcome)(?:\s+(.*)$)?')
    require_addressing = False
    help = u'welcome                         get the #stackato welcome package: links for downloads, docs, and support.\n\
welcome <nick>                   send another user the #stackato welcome package (staff only)'
    
    def init(self):
        self.staff = Staff(madcow=self.madcow)

    def response(self, nick, args, kwargs):
        kwargs[u'req'].make_private() # welcome package is always private
        cmd = args[0]
        target_nick = args[1].strip() if args[1] else None
        msg_nick = nick
            
        # only staff members & bot owner are allowed to set/change shortcuts
        if target_nick and (self.staff.is_staff(nick) or settings.OWNER_NICK == nick):
            kwargs['req'].set_sendto(target_nick)
            msg_nick = target_nick

        return u'Welcome to %s, %s!\n%s' % (kwargs[u'channel'], msg_nick, settings.WELCOME_MSG)