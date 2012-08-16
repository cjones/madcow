#!/usr/bin/env python

"""Setup script for Madcow bot"""

from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import sys
import os

if sys.hexversion < 0x02060000:
    raise ImportError('madcow requires at least version 2.6 of Python')

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


# just for fun, don't actually use this
def __supermagic_getversion(f):
    b = compile(open(f).read(), f, 'exec')
    d, c = __import__('dis'), b.co_code
    n, i, e, s = len(c), 0, 0, []
    while i < n:
        o, i = ord(c[i]), i + 1
        if o >= d.HAVE_ARGUMENT:
            a, e, i = ord(c[i]) + ord(c[i + 1]) * 256 + e, 0, i + 2
            if o == d.EXTENDED_ARG:
                e = a * 65536L
            if o in d.hasconst:
                s.append(b.co_consts[a])
            elif o in d.hasname:
                if b.co_names[a] == 'VERSION':
                    return '.'.join(map(str, s))
                s = []


def get_version(path):
    dwb, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        g = {'__file__': ''}
        exec compile(open(path, 'rb').read(), '', 'exec') in g
        return g.get('__version__', 'unknown')
    finally:
        sys.dont_write_bytecode = dwb


def main():
    root_dir = os.path.dirname(__file__)
    if root_dir != '':
        os.chdir(root_dir)
    version = get_version('madcow/__init__.py')
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
          author_email='cjones@gmail.com',
          url='https://github.com/cjones/madcow',
          description='Madcow infobot',
          license='GPL',
          version=version,
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
