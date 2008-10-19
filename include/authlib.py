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

from utils import Error
from random import randint
from hashlib import sha1
from base64 import b64encode, b64decode

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = ['UserNotFound', 'IllegalUserName', 'AuthLib']

class UserNotFound(Error):

    pass


class IllegalUserName(Error):

    pass


class AuthLib(object):

    def __init__(self, path):
        self.path = path

    def get_passwd(self):
        try:
            fo = open(self.path)
            try:
                data = fo.read()
            finally:
                fo.close()
        except:
            data = ''
        passwd = {}
        for line in data.splitlines():
            line = line.strip()
            if not len(line):
                continue
            username, password, flags = line.split(':')
            passwd[username] = {'password': password, 'flags': flags}
        return passwd

    def write_passwd(self, passwd):
        data = []
        for user, user_data in passwd.items():
            line = ':'.join([user, user_data['password'], user_data['flags']])
            data.append(line)
        data = '\n'.join(data) + '\n'
        fo = open(self.path, 'wb')
        try:
            fo.write(data)
        finally:
            fo.close()

    def change_flags(self, user, flags):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound
        passwd[user]['flags'] = flags
        self.write_passwd(passwd)

    def change_password(self, user, plain):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound
        passwd[user]['password'] = self.encrypt(plain)
        self.write_passwd(passwd)

    def add_user(self, user, plain, flags=''):
        if ':' in user:
            raise IllegalUserName, 'usernames cannot have : in them'
        if plain == None:
            password = '*'
        else:
            password = self.encrypt(plain)
        passwd = self.get_passwd()
        passwd[user] = {'password': password, 'flags': flags}
        self.write_passwd(passwd)

    def delete_user(self, user):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound, user
        del passwd[user]
        self.write_passwd(passwd)

    def check_user(self, user, plain):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound, user
        return self.check(passwd[user]['password'], plain)

    def user_exists(self, user):
        return user in self.get_passwd()

    def get_flags(self, user):
        passwd = self.get_passwd()
        if user not in passwd:
            raise UserNotFound, user
        return passwd[user]['flags']

    def encrypt(self, plain):
        digest, salt = self.get_digest(plain)
        return b64encode(salt + digest)

    def get_digest(self, plain, salt=None):
        if salt is None:
            salt = ''.join([chr(randint(0, 255)) for i in range(4)])
        return sha1(salt + plain).digest(), salt

    def check(self, encrypted, plain):
        if encrypted == '*':
            return False
        salted = b64decode(encrypted)
        salt, digest = salted[:4], salted[4:]
        return digest == self.get_digest(plain, salt)[0]

