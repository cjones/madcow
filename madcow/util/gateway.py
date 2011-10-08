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
import re
import socket
import datetime
from urlparse import urljoin
import errno
from madcow.util import Request, get_logger
from madcow.conf import settings
from madcow.util.text import encode, decode, get_encoding

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
        if not settings.GATEWAY_ENABLED:
            return
        self.log = get_logger('gateway', unique=False)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((settings.GATEWAY_ADDR, settings.GATEWAY_PORT))
        sock.listen(5)
        while self.bot.running:
            client, addr = sock.accept()
            self.log.info(u'connection from %s' % repr(addr))
            handler = GatewayServiceHandler(self, client, addr)
            handler.start()


class GatewayServiceHandler(Thread):

    """This class handles the listener service for message injection"""

    maxsize = 1 * 1024 * 1024 # 1 meg
    maxfiles = 9999
    bufsize = 8 * 1024
    timeout = 60
    newline = re.compile(r'\r?\n')
    headsep = re.compile(r'\r?\n\r?\n')
    safeword = re.compile(r'[^0-9a-z_.]', re.I)

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
                self.server.log.info(u'invalid payload from %s: %s' % (self.addr, error))
            except CloseConnection:
                self.server.log.info(u'closing connection to %s' % repr(self.addr))
            except ConnectionTimeout:
                self.server.log.info(u'connection timeout to %s' % repr(self.addr))
            except ConnectionClosed:
                self.server.log.info(u'connection closed by %s' % repr(self.addr))
            except Exception, error:
                self.server.log.warn(u'uncaught exception from %s: %s' % (self.addr, error))
                self.server.log.exception(error)
            break
        self.client.close()

    def data_received(self, data):
        self.buf += data
        if len(self.buf) > self.maxsize:
            raise InvalidPayload('payload exceeded max size')
        if not self.headers_done:
            if not self.headsep.search(self.buf):
                return
            try:
                # parse headers
                hdrs, self.buf = self.headsep.split(self.buf, 1)
                hdrs = decode(hdrs)
                hdrs = self.newline.split(hdrs)
                hdrs = [hdr.split(u':', 1) for hdr in hdrs]
                hdrs = [(k.lower(), v.lstrip()) for k, v in hdrs]
                hdrs = dict(hdrs)

                if u'size' in hdrs:
                    hdrs[u'size'] = int(hdrs[u'size'])

                # save data
                self.hdrs = hdrs
                self.headers_done = True
            except Exception, error:
                raise InvalidPayload(u'invalid payload: %s' % error)

        if u'size' in self.hdrs:
            if len(self.buf) < self.hdrs[u'size']:
                return
            self.hdrs[u'payload'] = self.buf[:self.hdrs[u'size']]

        self.process_message()
        raise CloseConnection

    def process_message(self):
        # see if we can reverse lookup sender
        modules = self.server.bot.modules.modules
        if 'learn' in modules:
            dbm = modules['learn']['obj'].get_db('email')
            for user, email in dbm.iteritems():
                if self.hdrs['from'] == email:
                    self.hdrs['from'] = user
                    break

        if u'payload' in self.hdrs:
            self.save_payload()

        if u'message' in self.hdrs:
            output = u'message from %s: %s' % (self.hdrs[u'from'],
                                               self.hdrs[u'message'])
            req = Request(message=output)
            req.colorize = False
            req.sendto = self.hdrs[u'to']
            self.server.bot.output(output, req)

    def save_payload(self):
        pad = len(str(self.maxfiles))
        imagepath = settings.GATEWAY_IMAGE_PATH
        baseurl = settings.GATEWAY_IMAGE_URL
        if not imagepath or not baseurl:
            raise InvalidPayload(u'images are not configured')

        filename = []
        if u'from' in self.hdrs:
            filename.append(self.hdrs[u'from'])
        filename.append(datetime.date.today().strftime(u'%Y-%m-%d'))
        if u'filename' in self.hdrs:
            filename.append(self.hdrs[u'filename'])

        filename = map(lambda x: self.safeword.sub(u'', x), filename)
        filename = filter(None, filename)
        filename = u'_'.join(filename)
        basename, ext = os.path.splitext(filename)
        basename = basename[:255 - (len(ext) + 1 + pad)]

        files = os.listdir(imagepath)
        filename = None
        for i in range(self.maxfiles):
            filename = basename
            if i:
                idx = str(i)
                filename += '_' + '0' * (pad - len(idx)) + idx
            filename += ext
            if not filename in files:
                break

        if not filename:
            raise InvalidPayload('no room for more files')

        with open(os.path.join(imagepath, filename), 'wb') as file:
            file.write(self.hdrs['payload'])

        message = urljoin(baseurl, filename)
        if u'message' in self.hdrs and self.hdrs[u'message']:
            message += u' (%s)' % self.hdrs[u'message']
        self.hdrs[u'message'] = message
