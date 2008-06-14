#!/usr/bin/env python

"""Mutate python script, add debug line to each function, print to STDOUT"""

import sys
from optparse import OptionParser
import re

def main():
    # parse args
    op = OptionParser()
    opts, args = op.parse_args()
    if len(args) != 1:
        op.error('missing file to modify')

    # read file
    fo = open(args[0], 'rb')
    try:
        data = fo.read()
    finally:
        fo.close()

    # regexes
    DefLine = re.compile(r'^(\s*)def\s+(\S+)\s*\(.*?\)\s*:\s*$')
    ClassLine = re.compile(r'^(\s*)class\s+(.*?)[ :(]')

    # parse
    linenum = 0
    class_name = None
    class_padding = 0
    for line in data.splitlines():

        # display the line
        sys.stdout.write(line + '\n')
        linenum += 1

        # classline?
        try:
            class_padding, class_name = ClassLine.search(line).groups()
            class_padding = len(class_padding)
        except:
            pass

        # def line?
        try:
            padding, funcname = DefLine.search(line).groups()
            padding = len(padding)
        except:
            continue

        # function must be indented to belong to class in question
        if padding <= class_padding:
            class_name = None
            class_padding = 0

        # XXX can this be autodetected? kind of a tricky problem.
        indent = 4

        # construct new line
        ipadding = ' ' * (padding + indent)
        name = '.'.join([i for i in class_name, funcname if i is not None])
        new = "%sprint 'DEBUG [%s] %s'\n" % (ipadding, linenum, name)
        sys.stdout.write(new)
        sys.stdout.flush()
        linenum += 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
