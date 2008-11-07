#!/usr/bin/env python

import sys

def main():
    assert len(sys.argv) == 2, u'need a filename'
    f = open(sys.argv[1], u'rb')
    try:
        data = f.read()
    finally:
        f.close()

    lines = data.splitlines()
    lines = map(lambda x: x.rstrip(), lines)
    lines = filter(lambda x: len(x), lines)
    lines.reverse()

    fixed = []
    for line in lines:
        fixed.append(line)
        if line.strip().startswith(u'def '):
            fixed.append(u'')
        elif line.strip().startswith(u'class '):
            fixed += [u'', u'']
    fixed.reverse()

    print u'\n'.join(fixed)

    return 0

if __name__ == u'__main__':
    sys.exit(main())
