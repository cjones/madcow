"""Generic passwd file authentication library"""

import random
import sha
import base64
import re

__version__ = '0.1'
__author__ = 'Christopher Jones <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = """
Copyright (C) 2007 Christopher Jones <cjones@gruntle.org>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""
__all__ = ['AuthLibError', 'AuthLib']

_re_comment = re.compile('#.*?$')


class AuthLibError(Exception):
    """Raised when there is a problem parsing the passwd file"""

    def __init__(self, error=None):
        self.error = error

    def __str__(self):
        return self.error


class AuthLib(object):
    """Core class for interfacing with the authentication system"""

    def __init__(self, file):
        self.file = file

    def add_user(self, user, passwd, extra=''):
        """Add or modify a user, optional dataline"""

        if ':' in user or '#' in user:
            raise AuthLibError, 'illegal username "%s": cannot contain # or :' % user

        passwd = self._encrypt(passwd)
        newline = ':'.join([user, passwd, extra])

        data = self._read_passwd()
        newdata = []
        added = False
        for line in data:
            parsed = self._parse_passwd_line(line)
            if parsed is not None and parsed['user'] == user:
                newdata.append(newline)
                added = True
            else:
                newdata.append(line)

        if added is False:
            newdata.append(newline)

        self._write_passwd(newdata)

    def verify_user(self, user, passwd):
        """Verify a users password"""

        data = self._read_passwd()
        for line in data:
            parsed = self._parse_passwd_line(line)
            if parsed is not None and parsed['user'] == user:
                if self._check(parsed['passwd'], passwd) is True:
                    return True

        return False

    def get_user_data(self, user):
        """Get extra dataline for user"""

        data = self._read_passwd()
        for line in data:
            parsed = self._parse_passwd_line(line)
            if parsed is not None and parsed['user'] == user:
                return parsed['extra']

    def _read_passwd(self):
        try:
            fo = open(self.file, 'rb')
            data = fo.read()
            fo.close()
            return data.splitlines()
        except:
            return []

    def _write_passwd(self, data=[]):
        try:
            fi = open(self.file, 'wb')
            for line in data:
                fi.write(line + '\n')
            fi.close()
        except Exception, e:
            raise AuthLibError, "couldn't write %s: %s" % (self.file, e)

    def _parse_passwd_line(self, line):
        line = line.strip()
        line = _re_comment.sub('', line)
        try:
            user, passwd, extra = line.split(':', 2)
            return { 'user': user, 'passwd': passwd, 'extra': extra }
        except:
            return None

    def _get_digest(self, plain, salt=None):
        if salt is None:
            salt = ''.join([chr(random.randint(0, 255)) for i in range(4)])

        return sha.new(salt + plain).digest(), salt

    def _encrypt(self, plain):
        digest, salt = self._get_digest(plain)
        return base64.b64encode(salt + digest)

    def _check(self, _encrypted, plain):
        salted = base64.b64decode(_encrypted)
        salt, digest = salted[:4], salted[4:]
        digest2, salt = self._get_digest(plain, salt)
        return digest == digest2

    def __str__(self):
        return '<AuthLib %s>' % self.file

    def __repr__(self):
        return str(self)


