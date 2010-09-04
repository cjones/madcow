#!/usr/bin/env python

"""TCP/IP proxy"""

from optparse import OptionParser
from threading import Thread
from select import select
from Queue import Queue
import socket
import errno
import sys
import os

__version__ = '0.1'

BLOCKSIZE = 4096
WORKERS = 5
QUEUE_SIZE = 5

class ConnectionClosed(Exception):

    pass


class ConnectionHandler(Thread):

    def __init__(self, server):
        super(ConnectionHandler, self).__init__()
        self.setDaemon(True)
        self.server = server
        self.start()

    def run(self):
        self.running = True
        print 'worker launched'
        try:
            while self.server.running:
                job = self.server.queue.get()
                if job is None:
                    break
                sock, addr = job
                print 'connection from %r' % (addr,)
                try:
                    self.handle(sock)
                except ConnectionClosed:
                    print 'connection to %r closed' % (addr,)
                except Exception, error:
                    print >> sys.stderr, error
        finally:
            self.running = False

    def handle(self, local):
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect(self.server.remote_addr)
        print 'remote connection to %r' % (self.server.remote_addr,)
        try:
            while True:
                rfds = select([local, remote], [], [], self.server.timeout)[0]
                if not rfds:
                    raise ConnectionClosed
                for sock in rfds:
                    try:
                        data = os.read(sock.fileno(), self.server.blocksize)
                    except (OSError, IOError), error:
                        if error.errno != errno.EIO:
                            raise
                        data = None
                    if not data:
                        raise ConnectionClosed
                    if sock is remote:
                        print 'sending to local: %r' % (data,)
                        local.send(data)
                    elif sock is local:
                        print 'sending to remote: %r' % (data,)
                        remote.send(data)
        finally:
            for sock in local, remote:
                try:
                    sock.close()
                except:
                    pass


class ProxyServer(object):

    """Docstring for ProxyServer"""

    def __init__(self, local_addr, remote_addr, queue_size=None, workers=None,
                 timeout=None, blocksize=None):
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        if queue_size is None:
            queue_size = QUEUE_SIZE
        self.queue_size = queue_size
        if workers is None:
            workers = WORKERS
        self.workers = workers
        self.timeout = timeout
        if blocksize is None:
            blocksize = BLOCKSIZE
        self.blocksize = blocksize
        self.running = False
        self.sock = None
        self.handlers = []

    def start(self):
        self.running = True
        self.queue = Queue()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.local_addr)
        self.sock.listen(self.queue_size)
        print 'server is listening on %r' % (self.local_addr,)
        self.handlers = [ConnectionHandler(self) for i in xrange(self.workers)]
        self.run()

    def run(self):
        while self.running:
            self.queue.put(self.sock.accept())
        self.stop()

    def stop(self):
        self.running = False
        while self.active_workers:
            self.queue.put(None)
        self.handlers = []
        if self.sock is not None:
            self.sock.close()

    @property
    def active_workers(self):
        return sum(1 for handler in self.handlers if handler.running)


def detach(server):
    if os.fork():
        os._exit(0)
    os.setsid()
    if os.fork():
        os._exit(0)
    import resource, signal
    for fd in xrange(resource.getrlimit(resource.RLIMIT_NOFILE)[0]):
        try:
            os.close(fd)
        except OSError, error:
            if error.errno != errno.EBADF:
                raise
    fd = os.open(os.devnull, os.O_RDWR)
    os.dup(fd)
    os.dup(fd)
    os.umask(027)
    os.chdir('/')
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)
    signal.signal(signal.SIGHUP,  signal.SIG_IGN)
    signal.signal(signal.SIGTERM, lambda *args, **kwargs: server.stop())


def main(argv=None):
    optparse = OptionParser('%prog [options] LOCALPORT REMOTEHOST REMOTEPORT',
                            description=__doc__, add_help_option=False)
    optparse.version = __version__
    optparse.add_option('-t', dest='timeout', metavar='FLOAT', type='float',
                        help='socket timeout in seconds (%default)')
    optparse.add_option('-d', dest='detach', default=False,
                        action='store_true', help='run as daemon')
    optparse.add_option('-a', dest='local_host', metavar='HOST',
                        default='localhost', help='bind address (%default)')
    optparse.add_option('-v', action='version',
                        help="show program's version number and exit")
    optparse.add_option('-h', action='help',
                        help='show this help message and exit')
    opts, args = optparse.parse_args(argv)
    if not args:
        optparse.print_help()
        return 2
    if len(args) != 3:
        optparse.error('invalid arguments')
    local_port, remote_host, remote_port = args
    def validate_port(port):
        if not port.isdigit():
            optparse.error('port must be an integer')
        port = int(port)
        if port < 1 or port > 65535:
            optparse.error('invalid port')
        return port
    try:
        server = ProxyServer((opts.local_host, validate_port(args[0])),
                             (args[1], validate_port(args[2])),
                             timeout=opts.timeout)
        if opts.detach:
            detach(server)
        try:
            server.start()
        finally:
            server.stop()
    except Exception, error:
        print >> sys.stderr, error
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
