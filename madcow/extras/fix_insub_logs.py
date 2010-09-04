#!/usr/bin/env python

"""Script to clean/normalize the #insub logfiles for megahal"""

import sys
import os
import re
from optparse import OptionParser


line_re = re.compile(r'^[0-9:\[\]]+\s+<(.*?)>\s+(.+)$')
log_new_re = re.compile(r'^madcow-irc-#?[hH]ugs-(\d{4})-(\d{2})-(\d{2})$')
log_old_re = re.compile(r'^insub\.log\.(\d{2})(\S{3})(\d{4})$')
month_map = dict(Jan='01', Feb='02', Mar='03', Apr='04', May='05', Jun='06',
                 Jul='07', Aug='08', Sep='09', Oct='10', Nov='11', Dec='12')


def logs(dir):
    for basedir, subdirs, filenames in os.walk(dir):
        for filename in filenames:
            path = os.path.join(basedir, filename)
            match = log_new_re.search(filename)
            if match:
                yield path, ''.join(match.groups())
                continue
            match = log_old_re.search(filename)
            if match:
                day, month, year = match.groups()
                yield path, year + month_map[month] + day
                continue
            print >> sys.stderr, 'skipping', filename


def main():
    parser = OptionParser()
    args = parser.parse_args()[1]
    if len(args) != 1:
        parser.error('missing log directory')
    for path, stamp in logs(args[0]):
        with open('clean.%s.log' % stamp, 'wb') as out:
            with open(path, 'rb') as file:
                for line in file:
                    try:
                        nick, message = line_re.search(line.strip()).groups()
                    except AttributeError:
                        continue
                    out.write('%s\t%s\n' % (nick.lower(), message))

    return 0


if __name__ == '__main__':
    sys.exit(main())
