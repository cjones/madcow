#!/usr/bin/env python

"""
Plugin for admin functionality which requires authentication

TODO:
- default flags in config
- user checking (don't let someone reregister)
- ability to change password
- flag in config to enable/disable the ability to register at all
- welcome message in config
- user/host identity passed in from protocol handlers (n!u@h, e.g.)
- authlib can raise user not found vs. password incorrect errors
- some kind of timeout for failed password attempts
- authlib can has default password policy
- TTL on being logged in? meh.. should log out people if they
  disconnect though.
"""

import sys
import re
import os
import time
from include.authlib import AuthLib

_reRegister = re.compile('^\s*register\s+(\S+)\s*$', re.I)
_reAuth = re.compile('^\s*(?:log[io]n|auth)\s+(\S+)\s*$', re.I)
_reFist = re.compile('^\s*fist\s+(\S+)\s+(.+)$', re.I)


class User(object):
    """This class represents a logged in user"""

    def __init__(self, user, flags):
        self.user = user
        self.flags = flags
        self.loggedIn = int(time.time())

    def isAdmin(self):
        return 'a' in self.flags

    def isRegistered(self):
        return True

    def __str__(self):
        return '<User %s>' % self.user

    def __repr__(self):
        return str(self)


class MatchObject(object):
    """This object is autoloaded by the bot"""

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.ns = ns
        self.dir = dir
        self.config = config

        self.enabled = True
        self.pattern = re.compile('^(.+)$')
        self.requireAddressing = False
        self.thread = False
        self.wrap = False
        self.help = None

        self.authlib = AuthLib('%s/data/db-%s-passwd' % (self.dir, self.ns))
        self.users = {}

    def response(self, **kwargs):
        if kwargs['private'] is not True:
            return

        nick = kwargs['nick']
        command = kwargs['args'][0]
        response = None

        # register
        try:
            passwd = _reRegister.search(command).group(1)
            return self.registerUser(nick, passwd)
        except:
            pass

        # log in
        try:
            passwd = _reAuth.search(command).group(1)
            return self.authenticateUser(nick, passwd)
        except:
            pass

        try:
            user = self.users[nick]
        except:
            return

        # admin functions
        if user.isAdmin():

            # be the puppetmaster
            try:
                channel, message = _reFist.search(command).groups()
                kwargs['req'].sendTo = channel
                return message
            except:
                pass

    def registerUser(self, user, passwd):
        self.authlib.add_user(user, passwd, 'r')
        return "LOLZ, you're registered! grats. try logging in now"

    def authenticateUser(self, user, passwd):
        if self.users.has_key(user):
            return 'You are already logged in.'

        status = self.authlib.verify_user(user, passwd)

        if status is False:
            return 'Nice try.. calling FBI'
        else:
            self.users[user] = User(user, self.authlib.get_user_data(user))
            return 'WELCOME. You can now.. do nothing special.'


