#!/usr/bin/env python

"""Terrible script i wrote while drunk that makes a standalone madcow"""

import sys
import os
from optparse import OptionParser
import re
import pty, select
import subprocess

_pyscript = re.compile(r'^(.*?)\.py$', re.I)
_prefix = '.'
_statics = {
    '_sample_config': 'madcow.ini-sample',
    '_grufti_data': 'grufti-responses.txt-sample',
}
_copyconfig = re.compile(r'^(\s*)shutil\.copyfile\(.*?,\s*(.+?)\)\s*$')
_loadmods = re.compile(r'^(\s*)filenames = os.walk\(self\.mod_dir\)\.next\(\)\[2\]\s*$')
_copyconfig_code = """fi = open(%s, 'wb')
try:
    fi.write(_sample_config)
finally:
    fi.close()"""
_loadmods_code = """if self.subdir == 'modules':
    filenames = _static_modules
elif self.subdir == 'periodic':
    filenames = _static_periodic"""
_grufti_code = """fi = open(%s, 'wb')
try:
    import madcow as bot
    fi.write(bot._grufti_data)
finally:
    fi.close()"""
_zipheader = """#!/bin/sh
python -c '
import sys
del sys.argv[0:2]
sys.path.insert(0, sys.argv[0])
import madcow
madcow.main()
' - $0 $@
exit

#zipfile
"""

def mkzip():
    lines = []
    for basedir, subdirs, filenames in os.walk(_prefix):
        for filename in filenames:
            if filename.endswith('.pyc'):
                path = os.path.join(basedir, filename)
                lines.append(path)
    pyclist = '\n'.join(lines) + '\n'

    p = subprocess.Popen('zip madcow -@'.split(), stdin=subprocess.PIPE)
    p.stdin.write(pyclist)
    p.stdin.close()
    p.wait()
    print 'done'

def mkbin():
    data = _zipheader + slurp('madcow.zip')
    fi = open('madcow', 'wb')
    try:
        fi.write(data)
    finally:
        fi.close()
    os.chmod('madcow', 0755)

def fix_modules():
    lines = []
    for subdir in ('modules', 'periodic',):
        dir = os.path.join(_prefix, subdir)
        basedir, subdirs, filenames = os.walk(dir).next()
        filenames = filter(lambda x: x.endswith('.py'), filenames)
        line = '_static_%s = %s' % (subdir, repr(filenames))
        lines.append(line)
    return lines

def slurp(filename):
    fo = open(filename, 'rb')
    try:
        return fo.read()
    finally:
        fo.close()

def add_statics():
    statics = []
    for varname, filename in _statics.items():
        statics.append('%s = %s' % (varname, repr(slurp(filename))))
    statics += fix_modules()
    mfile = os.path.join(_prefix, 'madcow.py')
    madcow = slurp(mfile).splitlines()
    for static in statics:
        i = madcow.index('# STATIC GLOBALS')
        madcow.insert(i+1, static)
    for i, line in enumerate(madcow):
        try:
            padding, dest = _copyconfig.search(line).groups()
        except:
            continue
        cfg = _copyconfig_code % dest
        cfg = cfg.splitlines()
        cfg = [padding + n for n in cfg]
        cfg = '\n'.join(cfg)
        madcow[i] = cfg

    for i, line in enumerate(madcow):
        try:
            padding = _loadmods.search(line).group(1)
        except:
            continue
        lm = _loadmods_code.splitlines()
        lm = [padding + n for n in lm]
        lm = '\n'.join(lm)
        madcow[i] = lm

    madcow = '\n'.join(madcow) + '\n'
    fi = open(mfile, 'wb')
    try:
        fi.write(madcow)
    finally:
        fi.close()
    gfile = os.path.join(_prefix, 'modules/grufti.py')
    grufti = slurp(gfile).splitlines()
    for i, line in enumerate(grufti):
        try:
            padding, dest = _copyconfig.search(line).groups()
        except:
            continue
        gc = _grufti_code % dest
        gc = gc.splitlines()
        gc = [padding + n for n in gc]
        gc = '\n'.join(gc)
        grufti[i] = gc
    grufti = '\n'.join(grufti) + '\n'
    fi = open(gfile, 'wb')
    try:
        fi.write(grufti)
    finally:
        fi.close()

def compile():
    scripts = {}
    for basedir, subdirs, filenames in os.walk(_prefix):
        for filename in filenames:
            try:
                name = _pyscript.search(filename).group(1)
            except:
                continue
            parts = basedir.split(os.path.sep)
            if parts[0] == _prefix:
                del parts[0]
            parts.append(name)
            name = '.'.join(parts)
            try:
                __import__(name, globals(), locals(), [])
            except Exception, e:
                print "couldn't import %s: %s" % (name, e)

def main():
    add_statics()
    compile()
    mkzip()
    mkbin()
    return 0

if __name__ == '__main__':
    sys.exit(main())
