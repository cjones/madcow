#!/usr/bin/env python

"""Setup script for Madcow bot"""

from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import sys
import os

if sys.hexversion < 0x02060000:
    raise ImportError('madcow requires at least version 2.6 of Python')
sys.dont_write_bytecode = True

from madcow import __version__

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


def main():
    root_dir = os.path.dirname(__file__)
    if root_dir != '':
        os.chdir(root_dir)
    packages = []
    data_files = []
    for basedir, subdirs, filenames in os.walk('madcow'):
        for subdir in list(subdirs):
            if subdir.startswith('.'):
                subdirs.remove(subdir)
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(basedir)))
        elif filenames:
            files = [os.path.join(basedir, filename) for filename in filenames
                     if os.path.splitext(filename)[1] not in ('.pyc', '.pyo')]
            data_files.append([basedir, files])

    setup(name='madcow',
          author='Chris Jones',
          author_email='cjones@gruntle.org',
          url='http://code.google.com/p/madcow/',
          description='Madcow infobot',
          license='GPL',
          version=__version__,
          packages=packages,
          data_files=data_files,
          scripts=['scripts/madcow'],
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
