"""Dummy class for non-threading platforms"""

from utils import Base
import logging as log

timeout = 3
__all__ = ['lock', 'launch_thread', 'stop_threads']

try:
    from threading import Thread, RLock, enumerate as get_threads
except:

    class Thread(Base):

        def start(self):
            log.error('threading not supported')


    class RLock(Base):

        def acquire(self):
            pass

        def release(self):
            pass


    def get_threads():
        return ()


lock = RLock()

def launch_thread(target, name=None, args=(), kwargs=None):
    thread = Thread(None, target, name, args, kwargs)
    thread.start()
    return thread

def stop_threads():
    for thread in get_threads():
        name = thread.getName()
        if name == 'MainThread':
            continue
        log.info('stopping %s' % name)
        thread.join(timeout)
        if thread.isAlive():
            log.warn('%s failed to stop, killing' % name)
            thread._Thread__stop()

