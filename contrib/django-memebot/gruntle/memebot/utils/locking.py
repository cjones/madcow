"""Generic locking mechanism"""

import tempfile
import time
import os
from django.conf import settings
from gruntle.memebot.utils import text, trapped

__all__ = ['LockError', 'Lock']

DEFAULT_TIMEOUT = None
DEFAULT_INTERVAL = 1
DEFAULT_LOCK_PERMS = 0644

class LockError(StandardError):

    """Raised when locking mechanism encounters a problem"""


class Lock(object):

    """Context manager: Wrap block of code in a file lock"""

    def __init__(self, name, timeout=None, lock_dir=None, interval=None, lock_perms=None, reentrant=False):
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        if lock_dir is None:
            lock_dir = settings.LOCK_DIR
        if interval is None:
            interval = DEFAULT_INTERVAL
        if lock_perms is None:
            lock_perms = DEFAULT_LOCK_PERMS
        self.name = name
        self.timeout = timeout
        self.lock_dir = lock_dir
        self.interval = interval
        self.lock_perms = lock_perms
        self.reentrant = reentrant
        self.pid = os.getpid()

    def get_lock_file(self):
        """Get lock file for this instance"""
        if not os.path.exists(self.lock_dir):
            os.makedirs(self.lock_dir)
        return os.path.join(self.lock_dir, self.name)

    lock_file = property(get_lock_file)

    def __enter__(self):
        """Enter context: Attempt to acquire lock"""
        lock_file = self.get_lock_file()
        start = time.time()
        last = 0
        while True:
            with trapped:
                if self.reentrant and os.path.exists(lock_file):
                    with open(lock_file, 'rb') as fp:
                        if text.cast(fp.read()) == self.pid:
                            break
                fd = os.open(lock_file, tempfile._text_openflags, self.lock_perms)
                try:
                    os.write(fd, text.encode(self.pid))
                finally:
                    os.close(fd)
                break
            now = time.time()
            if ((self.timeout is not None) and ((now - start) >= self.timeout)):
                raise LockError(text.format('unable to acquire lock for %s', self.name))
            sleep = self.interval - now + last
            if sleep > 0:
                time.sleep(sleep)
            last = now
        return self

    def __exit__(self, *exc_info):
        """Exit context: Release lock"""
        lock_file = self.get_lock_file()
        if os.path.exists(lock_file):
            with trapped:
                os.remove(lock_file)
