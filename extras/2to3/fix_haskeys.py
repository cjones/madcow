#!/usr/bin/env python

"""Fixes dict.has_key idiom to be 3.0 compliant"""

import sys
import os
import re
from optparse import OptionParser
import shutil

_splitext_re = re.compile(r'^(.+)\.([^.]+)$')
_haskey_re = re.compile(r'(if\s+(not\s+)?(\S+?)\.has_key\((.*?)\))')

def fix(path):
    with open(path, 'rb') as file:
        data = file.read()
    for match, hasnot, obj, key in _haskey_re.findall(data):
        new = ['if', key, 'in', obj]
        if hasnot:
            new.insert(2, 'not')
        data = data.replace(match, ' '.join(new))
        shutil.copy(path, path + '.orig')
        with open(path, 'wb') as file:
            file.write(data)
        print >> sys.stderr, 'fixed ' + path

def walk(dir):
    for basedir, subdirs, filenames in os.walk(dir):
        for filename in filenames:
            try:
                name, ext = _splitext_re.search(filename).groups()
            except AttributeError:
                continue
            yield os.path.join(basedir, filename), ext.lower()

def python_files(dir):
    for path, ext in walk(dir):
        if ext == 'py':
            yield path

def main():
    parser = OptionParser(usage='%prog <dir, ...>')
    paths = []
    for arg in parser.parse_args()[1]:
        if os.path.isdir(arg):
            paths += python_files(arg)
        elif os.path.isfile(arg):
            paths.append(arg)
    for path in paths:
        if os.path.abspath(path) == os.path.abspath(__file__):
            print >> sys.stderr, 'skipping clobber of source file'
            continue
        fix(path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
