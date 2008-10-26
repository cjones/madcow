#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

import sys
from optparse import OptionParser
import os
import re
import email
import mimetypes
import socket
from email.Header import decode_header
from useragent import geturl

# add madcow base directory to path
_basedir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))
sys.path.append(_basedir)

from include.utils import stripHTML
from madcow import Config

__version__ = '0.3'
__author__ = 'cj_ <cjones@gruntle.org>'

USAGE = '%prog [options] < email'
_configfile = os.path.join(_basedir, 'madcow.ini')

class GatewayDisabled(Exception):
    """Raised when gateway is disabled"""


class ParsingError(Exception):
    """Raised when email can't be parsed properly"""


class ConnectionError(Exception):
    """Raised when there is a problem sending to madcow listener"""


class EmailGateway(object):
    _spams = ('This is an MMS message. Please go to http://mms.telusmobility.com/do/LegacyLogin to view the message.', 'You have new Picture Mail!')
    _quoted = r'^(-+)\s*(original|forwarded)\s+(message|e?mail)\s*\1'
    _quoted = re.compile(_quoted, re.I)
    _sig = '--'
    _remove_quotes = re.compile('([\'"])(=\\?(?:[^\x00- ()<>@,;:"/\\[\\]?.=]+\\?){2}[!->@-~]+\\?=)\\1')

    def __init__(self, configfile=_configfile):
        config = Config(configfile).gateway
        if not config.enabled:
            raise GatewayDisabled
        self.service = (config.bind, config.port)
        self.channel = config.channel

    def parse_email(self, data):
        image = None
        message = email.message_from_string(data)
        text = None

        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            mime_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            if mime_type == 'image/jpeg':
                image = payload
            elif mime_type == 'text/html':
                if 'pictures.sprintpcs.com' in payload:
                    image = getsprint(payload)
                else:
                    text = stripHTML(payload)
            elif mime_type == 'text/plain':
                if 'You have new Picture Mail' not in payload:
                    text = payload

        # at this point, text could be None, '', or have something interesting
        try:
            text = [self.clean(text), self.clean(message['subject'])]
            text = filter(lambda x: isinstance(x, str), text)
            text = filter(lambda x: len(x), text)
            text = ' / '.join(text)
        except:
            pass

        # parse base64 encoded words and work around non-rfc2047 compliant
        # formats (google/blackberry)
        sender = message['from']
        sender = self._remove_quotes.sub(r'\2', sender)
        headers = decode_header(sender)
        header_parts = [unicode(part, charset or 'ascii') for part,
                charset in headers]
        sender = str(u' '.join(header_parts))

        headers = []
        headers.append('to: ' + self.channel)
        headers.append('from: ' + sender)
        if text:
            headers.append('message: ' + text)
        else:
            if image is None:
                raise ParsingError, "need a message for non-image mail"
        if image:
            headers.append('type: image')
            headers.append('size: %s' % len(image))

        output = '\r\n'.join(headers) + '\r\n\r\n'
        if image:
            output += image

        # send message to madcow service
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.service)
            s.send(output)
            s.close()
        except Exception, e:
            raise ConnectionError, 'problem injecting mail: %s' % e

    def clean(self, text):
        if text is None:
            return

        for spam in self._spams:
            if spam in text:
                text = text.replace(spam, '')
        text = text.strip()
        cleaned = []
        for line in text.splitlines():
            line = line.strip()
            if not len(line) or line.startswith('>'):
                continue
            elif self._quoted.search(line) or line == self._sig:
                break
            else:
                cleaned.append(line)
        text = ' '.join(cleaned)
        return text


# sprint PCS bullshit
spcs_piclink = re.compile(r'<a .*?href="(http://pictures.sprintpcs.com/share.do?.*?)">View Picture</a>', re.DOTALL)
spcs_thepic = re.compile(r'<img class="guestMediaImg".*?src="(http://pictures.sprintpcs.com(?::80)?/mmps/.*?)(?:\.jpg)?\?', re.DOTALL + re.I)

def getsprint(data):
    link = spcs_piclink.search(data).group(1)
    link = link.replace('&amp;', '&')
    page = geturl(link)
    picurl = spcs_thepic.search(page).group(1)
    image = geturl(picurl)
    return image

def main():
    op = OptionParser(version=__version__, usage=USAGE)
    op.add_option('-c', '--configfile', metavar='<file>', default=_configfile,
            help='default: %default')
    opts, args = op.parse_args()

    EmailGateway(configfile=opts.configfile).parse_email(sys.stdin.read())

    return 0

if __name__ == '__main__':
    sys.exit(main())
