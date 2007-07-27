"""
Module to help cut down on bot abuse. To wit:

from include.throttle import Throttle
t = Throttle()
def someRoutineInvokedByUser(user):
    name = 'unique name of this event to track'
    e = t.registerEvent(name=name, user=user)
    if e.isThrottled() is True:
        if t.warn() is True: displayWarningToUser()
        doNothing()
    else:
        doSomething()
"""

import time

class ThrottleStatus(object):
    def __init__(self, user=None, name=None, parent=None):
        self.parent = parent
        self.user = user
        self.name = name
        self.last = self.now
        self.count = 0
        self.warned = False
        self.throttled = False


    def getNow(self):
        return int(time.time())


    def getDelta(self):
        return self.now - self.last

    def isThrottled(self):
        if self.parent.enabled is False: return True

        if self.throttled is False: return False

        if self.delta > self.parent.ignore:
            self.count = 0
            self.warned = False
            self.throttled = False
            return False
        else:
            return True

    def warn(self):
        if self.warned is True:
            return False
        else:
            self.warned = True
            return True


    delta = property(getDelta)
    now = property(getNow)


class ThrottleEvent(object):
    def __init__(self, name=None, parent=None):
        self.name = name
        self.parent = parent
        self.cache = {}


    def status(self, user=None):
        if self.cache.has_key(user):
            status = self.cache[user]
        else:
            status = ThrottleStatus(user=user, name=self.name, parent=self.parent)

        self.cache[user] = status
        return status


class Throttle(object):
    def __init__(self, enabled=True, count=3, threshold=2, reduction=10, ignore=300):
        self.enabled = enabled
        self.count = count
        self.threshold = threshold
        self.reduction = reduction
        self.ignore = ignore
        self.cache = {}


    def event(self, name=None):
        if self.cache.has_key(name):
            event = self.cache[name]
        else:
            event = ThrottleEvent(name=name, parent=self)

        self.cache[name] = event
        return event


    def status(self, name=None, user=None):
        event = self.event(name)
        status = event.status(user)
        return status


    def registerEvent(self, name=None, user=None):
        status = self.status(name=name.lower(), user=user.lower())
        delta = status.delta
        status.last = status.now

        if delta < self.threshold:
            status.count += 1

            if status.count > self.count:
                status.throttled = True

        else:
            status.count -= int(delta / self.reduction)
            if status.count < 0: status.count = 0

        return status

