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
            log.info(u'GatewayService is disabled')
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.bot.config.gateway.bind, self.bot.config.gateway.port))
        sock.listen(5)
        while self.bot.running:
            client, addr = sock.accept()
            log.info(u'connection from %s' % repr(addr))
            handler = GatewayServiceHandler(self, client, addr)
            handler.start()


class GatewayServiceHandler(Thread):

    """This class handles the listener service for message injection"""

    maxsize = 1 * 1024 * 1024 # 1 meg
    bufsize = 8 * 1024
    timeout = 60
    newline = re.compile(r'\r?\n')
    headsep = re.compile(r'\r?\n\r?\n')
    safenick = re.compile(r'[^0-9a-z_]', re.I)
    required_headers = {u'message': (u'to', u'from', u'message'),
                        u'image': (u'to', u'from', u'size')}

    def __init__(self, server, client, addr):
        self.server = server
        self.client = client
        self.fd = client.fileno()
        self.addr = addr
        self.buf = u''
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
                data = u''
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
                log.info(u'invalid payload from %s: %s' % (self.addr, error))
            except CloseConnection:
                log.info(u'closing connection to %s' % repr(self.addr))
            except ConnectionTimeout:
                log.info(u'connection timeout to %s' % repr(self.addr))
            except ConnectionClosed:
                log.info(u'connection closed by %s' % repr(self.addr))
            except Exception, error:
                log.warn(u'uncaught exception from %s: %s' % (self.addr, error))
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
                hdrs = [hdr.split(u':', 1) for hdr in hdrs]
                hdrs = [(k.lower(), v.lstrip()) for k, v in hdrs]
                hdrs = dict(hdrs)

                # sanity check headers
                if u'type' in hdrs:
                    content_type = hdrs[u'type']
                else:
                    content_type = u'message'
                if content_type not in self.required_headers:
                    raise InvalidPayload(
                            u'unknown content type: ' + content_type)
                for header in self.required_headers[content_type]:
                    if header not in hdrs:
                        raise InvalidPayload(
                                u'missing required field ' + header)
                if u'size' in hdrs:
                    hdrs[u'size'] = int(hdrs[u'size'])

                # save data
                self.content_type = content_type
                self.hdrs = hdrs
                self.headers_done = True
            except Exception, error:
                raise InvalidPayload, u'invalid payload: %s' % error

        if self.content_type == u'image':
            if len(self.buf) < self.hdrs[u'size']:
                return
            image = self.buf[:self.hdrs[u'size']]
            self.save_image(image, self.hdrs)

        self.process_message(self.hdrs)
        raise CloseConnection

    def process_message(self, payload):
        # see if we can reverse lookup sender
        modules = self.server.bot.modules.dict()
        dbm = modules[u'learn'].get_db(u'email')
        for user, email in dbm.items():
            if payload[u'from'] == email:
                payload[u'from'] = user
                break

        output = u'message from %s: %s' % (
            payload[u'from'], payload[u'message']
        )

        req = Request(output)
        req.colorize = False
        req.sendto = payload[u'to']
        self.server.bot.output(output, req)

    def save_image(self, image, payload):
        if not self.isjpeg(image):
            print repr(image[:20])
            raise InvalidPayload, u'payload is not a JPEG image'
        imagepath = self.server.bot.config.gateway.imagepath
        baseurl = self.server.bot.config.gateway.imageurl
        if not imagepath or not baseurl:
            raise InvalidPayload, u'images are not configured'

        nick = self.safenick.sub(u'', payload[u'from'])[:16].lower()
        if not len(nick):
            raise InvalidPayload, u'invalid nick'

        date = datetime.date.today().strftime(u'%Y-%m-%d')
        basename = u'%s_%s' % (nick, date)
        idx = 0
        for basedir, subdirs, filenames in os.walk(imagepath):
            for filename in filenames:
                try:
                    name = filename.rsplit(u'.', 1)[0]
                    seq = int(name.split(basename + u'_', 1)[1])
                    if seq > idx:
                        idx = seq
                except:
                    continue
        idx += 1

        filename = u'%s_%s.jpg' % (basename, idx)
        fp = open(os.path.join(imagepath, filename), u'wb')
        try:
            fp.write(image)
        finally:
            fp.close()

        message = urljoin(baseurl, filename)
        if u'message' in payload and len(payload[u'message']):
            message += u' (%s)' % payload[u'message']
        payload[u'message'] = message

    def isjpeg(self, image):
        return image.startswith(u'\xff\xd8')
