#!/usr/bin/env python

"""Try to massage indentation"""

import sys
import re
from collections import defaultdict

INDENT = 4  # what we should set it to

_whitespace_re = re.compile(r'\s*')
_blank_re = re.compile(r'^\s+$')

class RedentError(Exception):

    pass


def main():
    data = sys.stdin.read()
    if '\t' in data:
        raise RedentError('omg tabs detected, fix that before running this')
    lines = data.splitlines()
    changes = defaultdict(int)
    last_indent = None
    parsed = []
    for line in lines:
        line = _blank_re.sub('', line)
        indent = len(_whitespace_re.match(line).group(0))
        tail = line[indent:]
        parsed.append((indent, tail))
        if last_indent is not None:
            change = last_indent - indent
            if change < 0:
                change *= -1
            if change:
                changes[change] += 1
        last_indent = indent
    changes = sorted(changes.iteritems(), key=lambda item: item[1],
                     reverse=True)
    detected_indent = changes[0][0]
    if detected_indent == INDENT:
        raise RedentError('no work needs to be done, indent level is same')
    for i, line in enumerate(parsed):
        indent, tail = line
        if indent % detected_indent:
            raise RedentError('uneven indentation detected')
        level = indent / detected_indent
        print (' ' * INDENT * level) + tail
    return 0

if __name__ == '__main__':
    sys.exit(main())
