#!/usr/bin/env python

"""
Convert normal megahal brain into one that uses longs instead of shorts.
This will allow you to use more than 65536 words.  To do this, change
the BYTE2 typedef from short to long.
"""

import sys
from optparse import OptionParser
from struct import pack, unpack

COOKIE = 'MegaHALv8'

def load_tree(fp):
    node = {'symbol': unpack('h', fp.read(2))[0],
            'usage': unpack('l', fp.read(4))[0],
            'count': unpack('h', fp.read(2))[0],
            'branch': unpack('h', fp.read(2))[0]}
    node['tree'] = [load_tree(fp) for i in xrange(node['branch'])]
    return node


def save_tree(fp, node):
    for key in 'symbol', 'usage', 'count', 'branch':
        fp.write(pack('l', node[key]))
    for child in node['tree']:
        save_tree(fp, child)


def main():
    optparse = OptionParser('%prog <brain> -o <output>')
    optparse.add_option('-o', dest='output', metavar='FILE', help='new brain')
    opts, args = optparse.parse_args()
    if not opts.output:
        optparse.error('you must specify an output file')
    if len(args) != 1:
        optparse.error('missing or invalid arguments')
    with open(args[0], 'rb') as fp:
        cookie = fp.read(len(COOKIE))
        if cookie != COOKIE:
            raise ValueError('not a megahal brain')
        order = unpack('b', fp.read(1))[0]
        forward = load_tree(fp)
        backward = load_tree(fp)
        words = [fp.read(unpack('b', fp.read(1))[0])
                 for i in xrange(unpack('l', fp.read(4))[0])]
    with open(opts.output, 'wb') as fp:
        fp.write(cookie)
        fp.write(pack('b', order))
        save_tree(fp, forward)
        save_tree(fp, backward)
        fp.write(pack('l', len(words)))
        for word in words:
            fp.write(pack('b', len(word)))
            fp.write(word)

    return 0

if __name__ == '__main__':
    sys.exit(main())
