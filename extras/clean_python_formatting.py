#!/usr/bin/env python

import sys

def main():
    assert len(sys.argv) == 2, 'need a filename'
    f = open(sys.argv[1], 'rb')
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
        if line.strip().startswith('def '):
            fixed.append('')
        elif line.strip().startswith('class '):
            fixed += ['', '']
    fixed.reverse()

    print '\n'.join(fixed)

    return 0

if __name__ == '__main__':
    sys.exit(main())
