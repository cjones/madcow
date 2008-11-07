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
import logging as log

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
        if self.parent.enabled is False: return False

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
            log.info(u'Throttling user %s for %s' % (self.user, self.name))
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
        if user in self.cache:
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
        if name in self.cache:
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
