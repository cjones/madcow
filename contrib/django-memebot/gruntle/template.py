#!/usr/bin/env python

# BEGIN django environment auto-configure
def setup_environ():
    """Initialize django environment from anywhere in project tree"""
    import sys, os
    from django.core.management import setup_environ
    path = os.path.abspath(__file__)
    while path and path != os.sep:
        path = os.path.dirname(path)
        if os.path.exists(os.path.join(path, 'settings.py')):
            break
    else:
        raise RuntimeError('Could not find a settings file')
    sys.path.insert(0, path)
    sys.dont_write_bytecode = True
    setup_environ(__import__('settings'))
setup_environ()
del setup_environ
# END django environment auto-configure

"""Documentation stub"""

#from django.db.models import Q
#from django.conf import settings
#from gruntle.memebot.models import *

def main():
    return 0

if __name__ == '__main__':
    exit(main())
