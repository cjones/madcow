#!/usr/bin/env python

"""Takes mail from procmail and sends it to local madcow service"""

import sys
import re
import socket
import email
import mimetypes

def main():
    send_to = '#hugs'
    payload = sys.stdin.read()

    #import time
    #filename = '/tmp/email-%s.txt' % int(time.time())
    #fi = open(filename, 'wb')
    #fi.write(payload)
    #fi.close()

    tags = re.compile(r'<[^>]+>')
    br = re.compile(r'<br[^>]*>')

    msg = email.message_from_string(payload)
    print msg['from']
    plain = html = None
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        filename = part.get_filename()
        mime_type = part.get_content_type()
        body = part.get_payload(decode=True)

        if mime_type == 'text/plain':
            plain = body

        if mime_type == 'text/html':
            html = body

    if plain:
        doc = plain
    elif html:
        html = br.sub('\n', html)
        html = tags.sub('', html)
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&nbsp;', ' ')
        doc = html
    else:
        doc = 'no message'

    nosig = []
    for line in doc.splitlines():
        line = line.strip()
        if not len(line):
            continue
        if line.strip() == '--':
            break
        nosig.append(line)

    output = 'to: %s\n' % send_to
    output += 'from: %s\n' % msg['from']
    output += 'message: %s' % ' '.join(nosig)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.send(output)
    s.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
