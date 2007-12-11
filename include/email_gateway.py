#!/usr/bin/env python

"""Takes mail from procmail and sends it to local madcow service"""

import sys
import re
import socket
import email
import mimetypes

def main():
    # static settings
    send_to = '#hugs'
    madcow_service = ('localhost', 5000)

    # get message from STDIN (for use with procmail)
    payload = sys.stdin.read()

    # XXX save copy of message body for debugging purposes
    #"""
    import time
    filename = '/tmp/email-%s.txt' % int(time.time())
    fi = open(filename, 'wb')
    fi.write(payload)
    fi.close()
    #"""

    # regexes for parsing
    tags = re.compile(r'<[^>]+>')
    br = re.compile(r'<br[^>]*>')
    quoted = re.compile(r'^(---+)\s*(original|forwarded)\s+(message|email)\s*\1', re.I)
    is_header = re.compile(r'^\S+:\s*.+$', re.I)
    telus_spam = 'This is an MMS message. Please go to http://mms.telusmobility.com/do/LegacyLogin to view the message.'

    # iterate over mime parts and extract likely message payloads
    msg = email.message_from_string(payload)
    plain = html = None
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        #filename = part.get_filename()
        mime_type = part.get_content_type()
        body = part.get_payload(decode=True)

        if mime_type == 'text/plain':
            plain = body

        if mime_type == 'text/html':
            html = body

    # use plain format if it exists, otherwise clean up html
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

    # strip out undesirable cruft like sigs, quoted messages
    nosig = []
    reading_quoted = False
    for line in doc.splitlines():
        line = line.strip()
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

    # remove spam from Telus carrier
    if telus_spam in message:
        message = message.replace(telus_spam, '')

    # construct payload for madcow
    output = 'to: %s\n' % send_to
    output += 'from: %s\n' % msg['from']
    output += 'message: %s' % message.strip()

    # send message to madcow service
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(madcow_service)
    s.send(output)
    s.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
