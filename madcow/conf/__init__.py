"""Wraps defaults settings with custom settings"""

import os
import sys

RELATIVE_PATHS = ['PIDFILE']

class Settings(object):

    def __init__(self):
        self.__loaded = False

    def __getattribute__(self, key):
        try:
            return super(Settings, self).__getattribute__(key)
        except AttributeError:
            if not self.__loaded:
                self.__load()
                return self.__getattribute__(key)

    def __load(self):
        base = os.environ.get('MADCOW_BASE', os.curdir)
        if base not in sys.path:
            sys.path.insert(0, base)
        import settings
        from madcow.conf import defaults
        for key in dir(defaults):
            if key.isupper():
                default = getattr(defaults, key)
                val = getattr(settings, key, default)
                if key in RELATIVE_PATHS:
                    val = os.path.join(base, val)
                setattr(self, key, val)
        self.__loaded = True

settings = Settings()
