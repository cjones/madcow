#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Handles authentication in Madcow"""

from __future__ import with_statement
from random import randint
from hashlib import sha1
from base64 import b64encode, b64decode
import os

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = ['UserNotFound', 'IllegalUserName', 'AuthLib']

class UserNotFound(Exception):

    pass


class IllegalUserName(Exception):

    pass


class AuthLib(object):

    def __init__(self, path, charset):
        self.path = path
        self.charset = charset

    def get_passwd(self):
        if os.path.exists(self.path):
            with open(self.path, 'rb') as file:
                data = file.read()
        else:
            data = ''
        passwd = {}
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            username, password, flags = map(self.decode, line.split(':'))
            passwd[username] = {u'password': password, u'flags': flags}
        return passwd

    def write_passwd(self, passwd):
        data = []
        for user, user_data in passwd.iteritems():
            line = u':'.join([user, user_data['password'], user_data['flags']])
            data.append(self.encode(line))
        with open(self.path, 'wb') as file:
            file.write('\n'.join(data) + '\n')

    def change_flags(self, user, flags):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound(user)
        passwd[user][u'flags'] = flags
        self.write_passwd(passwd)

    def change_password(self, user, plain):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound(user)
        passwd[user][u'password'] = self.encrypt(self.encode(plain))
        self.write_passwd(passwd)

    def add_user(self, user, plain, flags=''):
        if u':' in user:
            raise IllegalUserName(u'usernames cannot have : in them')
        passwd = self.get_passwd()
        passwd[user] = {u'password': self.encrypt(plain) if plain else u'*',
                        u'flags': flags}
        self.write_passwd(passwd)

    def delete_user(self, user):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound(user)
        del passwd[user]
        self.write_passwd(passwd)

    def check_user(self, user, plain):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound(user)
        return self.check(passwd[user][u'password'], plain)

    def user_exists(self, user):
        return user in self.get_passwd()

    def get_flags(self, user):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound(user)
        return passwd[user][u'flags']

    def encrypt(self, plain):
        digest, salt = self.get_digest(self.encode(plain))
        return self.decode(b64encode(salt + digest))

    def get_digest(self, plain, salt=None):
        if salt is None:
            salt = ''.join([chr(randint(0, 255)) for i in range(4)])
        return sha1(salt + plain).digest(), salt

    def check(self, encrypted, plain):
        if encrypted == '*':
            return False
        salted = b64decode(self.encode(encrypted))
        salt, digest = salted[:4], salted[4:]
        return digest == self.get_digest(self.encode(plain), salt)[0]

    def encode(self, data):
        if isinstance(data, unicode):
            data = data.encode(self.charset, 'replace')
        return data

    def decode(self, data):
        if isinstance(data, str):
            data = data.decode(self.charset, 'replace')
        return data

