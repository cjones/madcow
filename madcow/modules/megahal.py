#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""MegaHAL Interface"""

from include.utils import Module
import logging as log
import re
import os
import time

__version__ = u'0.2'
__author__ = u'Chris Jones <cjones@gruntle.org>'
__all__ = []

class MegaHALError(Exception):

    """Base MegaHAL Error"""


class InvalidID(MegaHALError):

    """Raised when an invalid ID is supplied"""


class Uninitialized(MegaHALError):

    """Raised if MegaHAL is not initialized"""


class BuildError(MegaHALError):

    """Raised when we try to build MegaHAL and it blows up"""


class MegaHAL(object):

    """MegaHAL Interface"""

    badchars_re = re.compile(r'[^a-z0-9_.]', re.I)
    update_freq = 1 * 60 * 60  # 1 hour
    update_max = 50

    def __init__(self, basedir, charset):
        self.basedir = basedir
        self.charset = charset
        self.brain = None
        self.last_updated = None
        self.last_changed = None
        self.updates = 0

    def setid(self, id):
        id = id.encode(self.charset, 'replace')
        id = self.badchars_re.sub('', id).lower()
        if not id:
            raise InvalidID(u'invalid or missing brain id')
        brain = os.path.join(self.basedir, id)
        exists = os.path.exists(brain)
        if self.brain:
            if not exists:
                raise InvalidID(u'unknown brain: ' + id)
            megahal.save()
            log.info('saved brain')
        if not exists:
            os.makedirs(brain)
            log.info(u'made megahal directory: ' + brain)
        log.debug('initializing brain with: ' + brain)
        megahal.init(brain)
        self.brain = brain
        return u'set brain to: ' + id

    def process(self, line):
        if not self.brain:
            raise Uninitialized('meghal is not initialized')
        if line == '#save':
            self.update()
            return 'I saved the brain'
        line = line.encode(self.charset, 'replace')
        response = megahal.process(line).decode(self.charset, 'replace')
        self.last_changed = time.time()
        self.updates += 1
        self.update_sentinel()
        return response

    def update_sentinel(self):
        if not self.last_updated:
            self.last_updated = time.time()
        update = False
        if self.last_changed - self.last_updated > self.update_freq:
            update = True
            log.debug('updating megahal because enough time has passed')
        if self.updates > self.update_max:
            update = True
            log.debug('updating because enough updates have happened')
        if update:
            self.update()

    def update(self):
        megahal.save()
        megahal.init(self.brain)
        self.last_updated = time.time()
        self.updates = 0


class Main(Module):

    pattern = re.compile(r'^\s*(brain|mh)\s+(.+?)\s*$', re.I)
    allow_threading = False
    help = u'mh <line> - talk to megahal'
    help += u'\nbrain <name> - switch to megahal brain'

    def __init__(self, madcow):

        # if megahal.so doesn't exist, let's try to build it
        global megahal
        try:
            from include import megahal
        except ImportError:
            log.warn("couldn't find megahal.so, i will try to build it")

            from subprocess import Popen, PIPE, STDOUT
            child = Popen(['./build.py'], stdout=PIPE, stderr=STDOUT,
                          cwd=os.path.join(madcow.prefix, 'include/pymegahal'))
            for line in child.stdout:
                try:
                    log.warn(line.strip())
                except:
                    pass
            child.wait()

            # let's try that again, shall we?
            try:
                from include import megahal
            except ImportError:
                raise BuildError('could not build MegaHAL automatically')

        # create the bot with a default personality
        self.megahal = MegaHAL(
                basedir=os.path.join(madcow.prefix, 'data/megahal'),
                charset=madcow.charset)
        self.megahal.setid('madcow')

    def response(self, nick, args, kwargs):
        try:
            command = args[0].lower()
            if command == u'brain':
                return self.megahal.setid(args[1])
            elif command == u'mh':
                return self.megahal.process(args[1])
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)

