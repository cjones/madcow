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

"""Handles gateway connections"""

from threading import Thread
import os
from select import select
from utils import Request
import re
import socket
import logging as log
import datetime
from urlparse import urljoin
import errno

class InvalidPayload(Exception):
    """Raised when invalid payload is received by gateway"""


class CloseConnection(Exception):
    """Raised to indicate gateway service should shut down connection"""


class ConnectionTimeout(Exception):
    """Raised when connection times out on read/write"""


class ConnectionClosed(Exception):
    """Raised when client closes their end"""


class GatewayService(object):

    """Gateway service spawns TCP socket and listens for requests"""

    def run(self):
        """While bot is alive, listen for connections"""
        if not self.bot.config.gateway.enabled:
            log.info('GatewayService is disabled')
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.bot.config.gateway.bind, self.bot.config.gateway.port))
        sock.listen(5)
        while self.bot.running:
            client, addr = sock.accept()
            log.info('connection from %s' % repr(addr))
            handler = GatewayServiceHandler(self, client, addr)
            handler.start()


class GatewayServiceHandler(Thread):

    """This class handles the listener service for message injection"""

    maxsize = 1 * 1024 * 1024 # 1 meg
    bufsize = 8 * 1024
    timeout = 60
    newline = re.compile(r'\r?\n')
    headsep = re.compile(r'\r?\n\r?\n')
    required_headers = {
        'message': ('to', 'from', 'message'),
        'image': ('to', 'from', 'size'),
    }
    safenick = re.compile(r'[^0-9a-z_]', re.I)

    def __init__(self, server, client, addr):
        self.server = server
        self.client = client
        self.fd = client.fileno()
        self.addr = addr
        self.buf = ''
        self.headers_done = False
        self.content_type = None
        self.hdrs = None
        self.size = 0
        Thread.__init__(self)
        self.setDaemon(True)

    def recv(self, size):
        if self.fd in select([self.fd], [], [], self.timeout)[0]:
            try:
                data = os.read(self.fd, size)
            except OSError, error:
                if error.errno != errno.EIO:
                    raise error
                data = ''
            if data:
                return data
            raise ConnectionClosed
        raise ConnectionTimeout

    def run(self):
        """Handles a TCP connection to gateway service"""
        while self.server.bot.running:
            try:
                if self.headers_done:
                    size = self.bufsize
                else:
                    size = 1
                data = self.recv(size)
                self.data_received(data)
                continue
            except InvalidPayload, error:
                log.info('invalid payload from %s: %s' % (self.addr, error))
            except CloseConnection:
                log.info('closing connection to %s' % repr(self.addr))
            except ConnectionTimeout:
                log.info('connection timeout to %s' % repr(self.addr))
            except ConnectionClosed:
                log.info('connection closed by %s' % repr(self.addr))
            except Exception, error:
                log.warn('uncaught exception from %s: %s' % (self.addr, error))
            break
        self.client.close()

    def data_received(self, data):
        self.buf += data
        if not self.headers_done:
            if not self.headsep.search(self.buf):
                return
            try:
                # parse headers
                hdrs, self.buf = self.headsep.split(self.buf, 1)
                hdrs = self.newline.split(hdrs)
                hdrs = [hdr.split(':', 1) for hdr in hdrs]
                hdrs = [(k.lower(), v.lstrip()) for k, v in hdrs]
                hdrs = dict(hdrs)

                # sanity check headers
                if 'type' in hdrs:
                    content_type = hdrs['type']
                else:
                    content_type = 'message'
                if content_type not in self.required_headers:
                    raise InvalidPayload(
                            'unknown content type: ' + content_type)
                for header in self.required_headers[content_type]:
                    if header not in hdrs:
                        raise InvalidPayload(
                                'missing required field ' + header)
                if 'size' in hdrs:
                    hdrs['size'] = int(hdrs['size'])

                # save data
                self.content_type = content_type
                self.hdrs = hdrs
                self.headers_done = True
            except Exception, error:
                raise InvalidPayload, 'invalid payload: %s' % error

        if self.content_type == 'image':
            if len(self.buf) < self.hdrs['size']:
                return
            image = self.buf[:self.hdrs['size']]
            self.save_image(image, self.hdrs)

        self.process_message(self.hdrs)
        raise CloseConnection

    def process_message(self, payload):
        # see if we can reverse lookup sender
        modules = self.server.bot.modules.dict()
        dbm = modules['learn'].get_db('email')
        for user, email in dbm.items():
            if payload['from'] == email:
                payload['from'] = user
                break

        output = 'message from %s: %s' % (
            payload['from'], payload['message']
        )

        req = Request(output)
        req.colorize = False
        req.sendto = payload['to']
        self.server.bot.output(output, req)

    def save_image(self, image, payload):
        if not self.isjpeg(image):
            print repr(image[:20])
            raise InvalidPayload, 'payload is not a JPEG image'
        imagepath = self.server.bot.config.gateway.imagepath
        baseurl = self.server.bot.config.gateway.imageurl
        if not imagepath or not baseurl:
            raise InvalidPayload, 'images are not configured'

        nick = self.safenick.sub('', payload['from'])[:16].lower()
        if not len(nick):
            raise InvalidPayload, 'invalid nick'

        date = datetime.date.today().strftime('%Y-%m-%d')
        basename = '%s_%s' % (nick, date)
        idx = 0
        for basedir, subdirs, filenames in os.walk(imagepath):
            for filename in filenames:
                try:
                    name = filename.rsplit('.', 1)[0]
                    seq = int(name.split(basename + '_', 1)[1])
                    if seq > idx:
                        idx = seq
                except:
                    continue
        idx += 1

        filename = '%s_%s.jpg' % (basename, idx)
        fp = open(os.path.join(imagepath, filename), 'wb')
        try:
            fp.write(image)
        finally:
            fp.close()

        message = urljoin(baseurl, filename)
        if 'message' in payload and len(payload['message']):
            message += ' (%s)' % payload['message']
        payload['message'] = message

    def isjpeg(self, image):
        return image.startswith('\xff\xd8')
