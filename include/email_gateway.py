#!/usr/bin/env python

"""Takes mail from procmail and sends it to local madcow service"""

import sys
import re
import socket

def main():
    payload = sys.stdin.read()

    re_sent_from = re.compile(r'^from:\s*(.+?)\s*$', re.I)
    sent_from = 'anonymous'
    send_to = '#hugs'
    body = []
    reading_body = False
    for line in payload.splitlines():
        try:
            sent_from = re_sent_from.search(line).group(1)
        except:
            pass

        if reading_body:
            body.append(line)

        if len(line) == 0:
            reading_body = True

    output = 'to: %s\n' % send_to
    output += 'from: %s\n' % sent_from
    output += 'message: %s' % ' '.join(body)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.send(output)
    s.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
