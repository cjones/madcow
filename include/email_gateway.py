#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Chris Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement
import sys
from optparse import OptionParser
import email
import email.header
import codecs
import os
import re
import socket

def find_madcow():
    """Find where we are run from and config file location"""
    prefix = sys.argv[0] if __file__.startswith(sys.argv[0]) else __file__
    prefix = os.path.dirname(prefix)
    prefix = os.path.abspath(prefix)
    parts = prefix.split(os.sep)
    while parts:
        prefix = os.sep.join(parts)
        config = os.path.join(prefix, 'madcow.ini')
        if os.path.exists(config):
            break
        parts.pop()
    return prefix, config

PREFIX, CONFIG = find_madcow()
sys.path.insert(0, PREFIX)

from include.utils import stripHTML
from madcow import Config

__version__ = '0.5'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

USAGE = '%prog < [email]'
newline_re = re.compile(r'[\r\n]+')
encoded_re = re.compile(r'(=\?.*?\?.*?\?.*?\?=)')
jpeg_ext_re = re.compile(r'^\.jp(e?g|e)$', re.I)

def lookup_charset(charset):
    """See if we support this encoding, or return default one"""
    try:
        return codecs.lookup(charset).name
    except (LookupError, TypeError, AttributeError):
        return sys.getdefaultencoding()


def decode_header(line):
    """Decode MIME header"""
    parts = []
    if line:
        for part in encoded_re.split(line):
            decoded = []
            for word, charset in email.header.decode_header(part):
                decoded.append(word.decode(lookup_charset(charset), 'replace'))
            parts.append(u' '.join(decoded))
    return u''.join(parts)


def main():
    """Parse email and send to gateway"""

    # read argv
    parser = OptionParser(version=__version__, usage=USAGE)
    parser.add_option('-c', '--config', metavar='<file>', default=CONFIG,
                      help='location of config (%default)')
    opts, args = parser.parse_args()

    # get gateway information from config
    config = Config(opts.config)
    if not config.gateway.enabled:
        print >> sys.stderr, 'error: gateway is disabled'
        return 1
    service = (config.gateway.bind, config.gateway.port)
    channel = config.gateway.channel
    output_encoding = lookup_charset(config.main.charset)

    # parse MIME email
    message = email.message_from_file(sys.stdin)
    body = set()
    images = []
    for part in message.walk():
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        type = part.get_content_type()
        maintype, subtype = type.split('/')

        # is a jpeg file
        if payload.startswith('\xff\xd8'):
            filename = decode_header(part.get_filename())
            filename = filename.encode(output_encoding, 'replace')
            if not filename:
                filename = 'unknown.jpg'
            basename, ext = os.path.splitext(filename)
            if not jpeg_ext_re.match(ext):
                ext = '.jpg'
            filename = basename + ext
            images.append((filename, payload))

        # possible message
        elif maintype == 'text':
            charset = lookup_charset(part.get_content_charset())
            payload = payload.decode(charset, 'replace')
            if subtype == 'html':
                payload = stripHTML(payload)
            payload = map(lambda item: item.strip(), payload.splitlines())
            if u'--' in payload:
                payload = payload[:payload.index(u'--')]
            payload = u' '.join(filter(None, payload))
            body.add(payload.encode(output_encoding, 'replace'))

    sender = decode_header(message['from']).encode(output_encoding, 'replace')
    headers = ['from: %s' % sender, 'to: %s' % channel]
    body = sorted(body, key=lambda item: len(item), reverse=True)
    if body:
        headers.append('message: %s' % body[0])

    messages = []
    if images:
        for filename, payload in images:
            message = list(headers)
            message.append('filename: %s' % filename)
            message.append('size: %d' % len(payload))
            message = '\n'.join(message) + '\n\n' + payload
            messages.append(message)
    else:
        messages.append('\n'.join(headers) + '\n\n')

    for message in messages:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(service)
        client.send(message)
        client.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
