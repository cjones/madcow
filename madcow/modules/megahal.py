"""MegaHAL Interface"""

import re
import os
import time
import sys
from madcow.util import Module
from madcow.util.textenc import *
import shutil

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

    def __init__(self, basedir, logger=None, srcdb=None):
        self.basedir = basedir
        self.brain = None
        self.last_updated = None
        self.last_changed = None
        self.updates = 0
        self.log = logger
        self.srcdb = srcdb

    def setid(self, id):
        id = encode(id)
        id = self.badchars_re.sub('', id).lower()
        if not id:
            raise InvalidID(u'invalid or missing brain id')
        brain = os.path.join(self.basedir, id)
        exists = os.path.exists(brain)
        if self.brain:
            if not exists:
                raise InvalidID(u'unknown brain: ' + id)
            megahal.save()
            self.log.info('saved brain')
        if not exists:
            os.makedirs(brain)
            self.log.info(u'made megahal directory: ' + brain)
            for filename in os.listdir(self.srcdb):
                if filename.startswith('megahal.'):
                    shutil.copy(os.path.join(self.srcdb, filename), os.path.join(brain, filename))
        self.log.debug('initializing brain with: ' + brain)
        megahal.init(brain)
        self.brain = brain
        return u'set brain to: ' + id

    def process(self, line):
        if not self.brain:
            raise Uninitialized('meghal is not initialized')
        if line == '#save':
            self.update()
            return 'I saved the brain'
        line = encode(line)
        response = decode(megahal.process(line))
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
            self.log.debug('updating megahal because enough time has passed')
        if self.updates > self.update_max:
            update = True
            self.log.debug('updating because enough updates have happened')
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
    help = u'\n'.join([
        u'mh <line> - talk to megahal',
        u'brain <name> - switch to megahal brain',
        u'mh #save - force sync of brain to disk',
        ])

    def init(self):
        src = os.path.join(self.madcow.prefix, 'include', 'pymegahal')

        # if megahal.so doesn't exist, let's try to build it
        global megahal
        try:
            import cmegahal as megahal
        except ImportError:
            self.log.warn("couldn't find cmegahal.so, i will try to build it")
            from subprocess import Popen, PIPE, STDOUT
            from tempfile import mkdtemp
            from shutil import rmtree
            tmp = mkdtemp()
            try:
                p = Popen([sys.executable, 'setup.py', 'build', '--build-base', tmp, '--build-lib', self.madcow.base],
                          cwd=src, stdout=PIPE, stderr=STDOUT)
                for line in p.stdout:
                    self.log.warn(line)
                p.wait()
            finally:
                if os.path.exists(tmp):
                    rmtree(tmp)

            # let's try that again, shall we?
            try:
                import cmegahal as megahal
            except ImportError:
                raise BuildError('could not build MegaHAL automatically')

        # create the bot with a default personality
        default = os.path.join(self.madcow.base, 'db', 'megahal')
        self.megahal = MegaHAL(basedir=default, logger=self.log, srcdb=os.path.join(src, 'db'))
        self.megahal.setid('madcow')

    def response(self, nick, args, kwargs):
        command = args[0].lower()
        if command == u'brain':
            return self.megahal.setid(args[1])
        elif command == u'mh':
            return self.megahal.process(args[1])
