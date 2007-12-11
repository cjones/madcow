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

    #"""
    import time
    filename = '/tmp/email-%s.txt' % int(time.time())
    fi = open(filename, 'wb')
    fi.write(payload)
    fi.close()
    #"""

    tags = re.compile(r'<[^>]+>')
    br = re.compile(r'<br[^>]*>')
    quoted = re.compile(
            r'^(---+)\s*(original|forwarded)\s+(message|email)\s*\1', re.I)
    is_header = re.compile(r'^\S+:\s*.+$', re.I)
    telus_spam = 'This is an MMS message. Please go to http://mms.telusmobility.com/do/LegacyLogin to view the message.'

    msg = email.message_from_string(payload)
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
    reading_quoted = False
    for line in doc.splitlines():
        line = line.strip()
        #print '>>> %s' % repr(line)
        if not len(line):
            continue
        if line.startswith('>'):
            continue
        if quoted.search(line):
            reading_quoted = True
            continue
        if reading_quoted:
            if is_header.search(line):
                continue
            else:
                reading_quoted = False
        if line == '--':
            break
        nosig.append(line)

    message = ' '.join(nosig)

    if telus_spam in message:
        message = message.replace(telus_spam, '')

    message = message.strip()

    output = 'to: %s\n' % send_to
    output += 'from: %s\n' % msg['from']
    output += 'message: %s' % message

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    s.send(output)
    s.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
