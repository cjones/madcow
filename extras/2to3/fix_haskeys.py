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
    with open(path, u'rb') as file:
        data = file.read()
    for match, hasnot, obj, key in _haskey_re.findall(data):
        new = [u'if', key, u'in', obj]
        if hasnot:
            new.insert(2, u'not')
        data = data.replace(match, u' '.join(new))
        shutil.copy(path, path + u'.orig')
        with open(path, u'wb') as file:
            file.write(data)
        print >> sys.stderr, u'fixed ' + path

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
        if ext == u'py':
            yield path

def main():
    parser = OptionParser(usage=u'%prog <dir, ...>')
    paths = []
    for arg in parser.parse_args()[1]:
        if os.path.isdir(arg):
            paths += python_files(arg)
        elif os.path.isfile(arg):
            paths.append(arg)
    for path in paths:
        if os.path.abspath(path) == os.path.abspath(__file__):
            print >> sys.stderr, u'skipping clobber of source file'
            continue
        fix(path)
    return 0

if __name__ == u'__main__':
    sys.exit(main())
