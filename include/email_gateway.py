#!/usr/bin/env python

import sys
from optparse import OptionParser
import os
import re
import email
import mimetypes
import socket
from email.Header import decode_header

# add madcow base directory to path
_basedir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))
sys.path.append(_basedir)

from include.utils import Base, Error, stripHTML
from madcow import Config

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Chris Jones'
__usage__ = '%prog [options] < email'
_configfile = os.path.join(_basedir, 'madcow.ini')

class GatewayDisabled(Error):
    """Raised when gateway is disabled"""


class ParsingError(Error):
    """Raised when email can't be parsed properly"""


class ConnectionError(Error):
    """Raised when there is a problem sending to madcow listener"""


class EmailGateway(Base):
    _spams = ('This is an MMS message. Please go to http://mms.telusmobility.com/do/LegacyLogin to view the message.',)
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

    def parse_email(self, payload):
        try:
            message = email.message_from_string(payload)
            for part in message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                mime_type = part.get_content_type()
                body = part.get_payload(decode=True)
                if mime_type == 'text/plain':
                    break
                elif mime_type == 'text/html':
                    body = stripHTML(body)
                    break

            for spam in self._spams:
                if spam in body:
                    body = body.replace(spam, '')

            body = body.strip()
            cleaned = []
            for line in body.splitlines():
                line = line.strip()
                if not len(line) or line.startswith('>'):
                    continue
                elif self._quoted.search(line) or line == self._sig:
                    break
                else:
                    cleaned.append(line)
            body = ' '.join(cleaned)
        except Exception, e:
            raise ParsingError, "couldn't parse payload: %s" % e

        sender = message['from']
        sender = self._remove_quotes.sub(r'\2', sender)
        headers = decode_header(sender)
        header_parts = [unicode(part, charset or 'ascii') for part,
                charset in headers]
        sender = str(u' '.join(header_parts))

        # send message to madcow service
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.service)
            s.send('to: %s\n' % self.channel)
            s.send('from: %s\n' % sender)
            s.send('message: %s\n' % body)
            s.close()
        except Exception, e:
            raise ConnectionError, 'problem injecting mail: %s' % e


def main():
    op = OptionParser(version=__version__, usage=__usage__)
    op.add_option('-c', '--configfile', metavar='<file>', default=_configfile,
            help='default: %default')
    opts, args = op.parse_args()

    EmailGateway(configfile=opts.configfile).parse_email(sys.stdin.read())

    return 0

if __name__ == '__main__':
    sys.exit(main())
