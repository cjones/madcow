#!/usr/bin/env python

"""
Plugin for admin functionality which requires authentication

TODO:
- user checking (don't let someone reregister)
- ability to change password
- user/host identity passed in from protocol handlers (n!u@h, e.g.)
- authlib can raise user not found vs. password incorrect errors
- some kind of timeout for failed password attempts
- authlib can has default password policy
- TTL on being logged in? meh.. should log out people if they disconnect though.
"""

import sys
import re
import os
import time
from include.authlib import AuthLib

_reRegister = re.compile('^\s*register\s+(\S+)\s*$', re.I)
_reAuth = re.compile('^\s*(?:log[io]n|auth)\s+(\S+)\s*$', re.I)
_reFist = re.compile('^\s*fist\s+(\S+)\s+(.+)$', re.I)
_reHelp = re.compile('^\s*admin\s+help\s*$', re.I)
_reLogout = re.compile('^\s*log(?:out|off)\s*$', re.I)

_usage =  'admin help - this screen\n'
_usage += 'register <pass> - register with bot\n'
_usage += 'login <pass> - login to bot\n'
_usage += 'fist <chan> <msg> - make bot say something in channel\n'
_usage += 'logout - log out of bot'


class User(object):
    """This class represents a logged in user"""

    def __init__(self, user, flags):
        self.user = user
        self.flags = flags
        self.loggedIn = int(time.time())

    def isAdmin(self):
        return 'a' in self.flags

    def isRegistered(self):
        if 'a' in self.flags or 'r' in self.flags:
            return True
        else:
            return False

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

        if self.config.admin.enabled is not True:
            self.enabled = False

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

        # don't pass this point unless we are logged in
        try:
            user = self.users[nick]
        except:
            return

        # logout
        if _reLogout.search(command):
            del self.users[nick]
            return 'You are now logged out.'

        # help
        if _reHelp.search(command):
            return _usage

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
        if self.config.admin.allowRegistration is True:
            flags = self.config.admin.defaultFlags
            if flags is None:
                flags = 'r'

            self.authlib.add_user(user, passwd, flags)
            return "You are now registered, try logging in: login <pass>"
        else:
            return "Registration is disabled."

    def authenticateUser(self, user, passwd):
        status = self.authlib.verify_user(user, passwd)

        if status is False:
            return 'Nice try.. notifying FBI'
        else:
            self.users[user] = User(user, self.authlib.get_user_data(user))
            return 'You are now logged in. Message me "admin help" for help'


