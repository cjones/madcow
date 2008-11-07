#!/usr/bin/env python

import sys
import optparse
import os
import tempfile
import subprocess

def paths():
    for arg in optparse.OptionParser().parse_args()[1]:
        if os.path.isdir(arg):
            for basedir, subdirs, filenames in os.walk(arg):
                for filename in filenames:
                    yield os.path.join(basedir, filename)
        elif os.path.isfile(arg):
            yield arg


def pyfiles():
    for path in paths():
        if os.stat(path).st_ino == os.stat(__file__).st_ino:
            print '>>> skipping %s' % path
            continue
        filename = os.path.basename(path)
        if filename.endswith('.py'):
            with open(path, 'rb') as file:
                data = file.read()
                lines = [line.rstrip() for line in data.splitlines()]
                yield path, lines


def fix():
    quotes = tuple('"\'')
    for path, lines in pyfiles():
        fixed_lines = []
        multiline = None
        for line in lines:
            fixed = line
            line = list(line)
            pos = 0
            start = None
            isuni = False
            quote = lambda: line[start]
            while pos < len(line):
                prev = line[pos - 1] if pos else None
                ch = line[pos]
                next = line[pos + 1] if pos < len(line) - 1 else None
                isquote = ch in quotes

                if multiline:
                    if ''.join(line[pos:pos + 3]) == multiline * 3:
                        pos += 3
                        multiline = None
                        start = None
                        isuni = False
                elif start is not None:  # in a quote
                    if ch == quote():  # possible terminator
                        if next == quote(): # multiline
                            multiline = ch
                            pos += 1
                        elif prev != '\\':
                            if not isuni:
                                substr = line[start:pos + 1]
                                substr = ''.join(substr)
                                fixed = fixed.replace(substr, 'u' + substr)
                            start = None
                            isuni = False
                elif isquote:
                    start = pos
                    if prev in ('r', 'u'):
                        isuni = True
                pos += 1
            fixed = fixed.replace('str(', 'unicode(')
            fixed_lines.append(fixed)
        fixed = '\n'.join(fixed_lines) + '\n'
        fd, tmp = tempfile.mkstemp()
        os.write(fd, fixed)
        os.close(fd)
        args = ['diff', '-u', path, tmp]
        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        diff = process.stdout.read()
        os.remove(tmp)

        diff = diff.replace('+++ ' + tmp, '+++ ' + path)
        print diff


def main():
    fix()
    return 0

if __name__ == '__main__':
    sys.exit(main())
