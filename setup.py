#!/usr/bin/env python

"""Setup script for Madcow bot"""

from distutils.core import setup
import sys

if sys.hexversion < 0x02060000:
    raise ImportError('madcow requires at least version 2.6 of Python')
sys.dont_write_bytecode = True

from madcow import __version__

def main():
    setup(name='madcow',
          author='Chris Jones',
          author_email='cjones@gruntle.org',
          url='http://code.google.com/p/madcow/',
          description='Madcow infobot',
          license='GPL',
          version=__version__,
          packages=['madcow'],
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Environment :: Console',
                       'License :: OSI Approved :: GNU General Public License (GPL)',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python :: 2.6',
                       'Topic :: Communications :: Chat :: AOL Instant Messenger',
                       'Topic :: Communications :: Chat :: Internet Relay Chat'])

    return 0

if __name__ == '__main__':
    sys.exit(main())
