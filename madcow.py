#!/usr/bin/env python

__version__ = '1.1.3'
__author__ = 'Christopher Jones <cjones@gruntle.org>'
__copyright__ = """
Copyright (C) 2007 Christopher Jones <cjones@gruntle.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""

import sys
import os
from ConfigParser import ConfigParser
from optparse import OptionParser
import re
import threading
import time
import logging
from include.authlib import AuthLib
import SocketServer
import select

class Request(object):
    """
    Generic object passed in from protocol handlers for processing
    """

    def __init__(self, message=None):

        self.message = message

        # required attributes get a default
        self.nick = None
        self.addressed = False
        self.correction = False
        self.channel = None
        self.args = []

    def __getattr__(self, attr):
        return None


class User(object):
    """This class represents a logged in user"""

    def __init__(self, user, flags):
        self.user = user
        self.flags = flags
        self.loggedIn = int(time.time())

    def isAdmin(self):
        return 'a' in self.flags

    def isRegistered(self):
        if 'a' in self.flags or 'r' in self.flags:
            return True
        else:
            return False

    def __str__(self):
        return '<User %s>' % self.user

    def __repr__(self):
        return str(self)


class Admin(object):
    """Class to handle admin interface"""

    _reRegister = re.compile('^\s*register\s+(\S+)\s*$', re.I)
    _reAuth = re.compile('^\s*(?:log[io]n|auth)\s+(\S+)\s*$', re.I)
    _reFist = re.compile('^\s*fist\s+(\S+)\s+(.+)$', re.I)
    _reHelp = re.compile('^\s*admin\s+help\s*$', re.I)
    _reLogout = re.compile('^\s*log(?:out|off)\s*$', re.I)

    _usage =  'admin help - this screen\n'
    _usage += 'register <pass> - register with bot\n'
    _usage += 'login <pass> - login to bot\n'
    _usage += 'fist <chan> <msg> - make bot say something in channel\n'
    _usage += 'logout - log out of bot'

    def __init__(self, bot):
        self.bot = bot
        self.authlib = AuthLib('%s/data/db-%s-passwd' % (bot.dir, bot.ns))
        self.users = {}
        self.modules = {}
        self.usageLines = Admin._usage.splitlines()

    def parse(self, req):
        if self.bot.config.admin.enabled is not True:
            return

        nick = req.nick
        command = req.message
        response = None

        # register
        try:
            passwd = Admin._reRegister.search(command).group(1)
            return self.registerUser(nick, passwd)
        except:
            pass

        # log in
        try:
            passwd = Admin._reAuth.search(command).group(1)
            return self.authenticateUser(nick, passwd)
        except:
            pass

        # don't pass this point unless we are logged in
        try:
            user = self.users[nick]
        except:
            return

        # logout
        if Admin._reLogout.search(command):
            del self.users[nick]
            return 'You are now logged out.'

        # help
        if Admin._reHelp.search(command):
            return '\n'.join(self.usageLines)

        # admin functions
        if user.isAdmin():

            # be the puppetmaster
            try:
                channel, message = Admin._reFist.search(command).groups()
                req.sendTo = channel
                return message
            except:
                pass

    def registerUser(self, user, passwd):
        if self.bot.config.admin.allowRegistration is True:
            flags = self.bot.config.admin.defaultFlags
            if flags is None:
                flags = 'r'

            self.authlib.add_user(user, passwd, flags)
            return "You are now registered, try logging in: login <pass>"
        else:
            return "Registration is disabled."

    def authenticateUser(self, user, passwd):
        status = self.authlib.verify_user(user, passwd)

        if status is False:
            return 'Nice try.. notifying FBI'
        else:
            self.users[user] = User(user, self.authlib.get_user_data(user))
            return 'You are now logged in. Message me "admin help" for help'


class ServiceHandler(SocketServer.BaseRequestHandler):

    re_from = re.compile(r'^from:\s*(.+?)\s*$', re.I)
    re_to = re.compile(r'^to:\s*(#\S+)\s*$', re.I)
    re_message = re.compile(r'^message:\s*(.+?)\s*$', re.I)

    def setup(self):
        logging.info('connection from %s' % repr(self.client_address))

    def handle(self):
        data = ''
        while True:
            read = self.request.recv(1024)
            if len(read) == 0:
                break
            data += read
        logging.info('got payload: %s' % repr(data))

        sent_from = send_to = message = None
        for line in data.splitlines():
            try:
                sent_from = ServiceHandler.re_from.search(line).group(1)
            except:
                pass

            try:
                send_to = ServiceHandler.re_to.search(line).group(1)
            except:
                pass

            try:
                message = ServiceHandler.re_message.search(line).group(1)
            except:
                pass

        if sent_from is None or send_to is None or message is None:
            logging.warn('invalid payload')
            return

        # see if we can reverse lookup sender
        db = self.server.madcow.modules['learn'].get_db('email')
        for user, email in db.items():
            if sent_from == email:
                sent_from = user
                break

        req = Request()
        req.colorize = False
        req.wrap = False
        req.sendTo = send_to
        output = 'message from %s: %s' % (sent_from, message)
        self.server.madcow.output(output, req)

    def finish(self):
        logging.info('connection closed by %s' % repr(self.client_address))


class Madcow(object):
    """
    Core bot handler
    """
    reDelim = re.compile(r'\s*[,;]\s*')

    def __init__(self, config=None, dir=None):
        self.config = config
        self.dir = dir

        self.ns = self.config.modules.dbnamespace
        self.ignoreModules = [ '__init__', 'template' ]
        self.ignoreModules.append('tac')       # moved to grufti framework in 1.0.7
        self.ignoreModules.append('bullshitr') # moved to grufti framework in 1.0.7
        self.ignoreModules.append('ircadmin')  # moved to core bot
        self.moduleDir = self.dir + '/modules'
        self.outputLock = threading.RLock()

        if self.config.main.ignorelist is not None:
            self.ignoreList = [nick.lower() for nick in Madcow.reDelim.split(self.config.main.ignorelist)]
            logging.info('Ignoring nicks: %s' % ', '.join(self.ignoreList))
        else:
            self.ignoreList = []

        self.admin = Admin(self)

        # dynamically generated content
        self.usageLines = []
        self.modules = {}
        self.loadModules()

        # start local service for handling requests
        threading.Thread(target=self.startService).start()

    def startService(self, *args, **kwargs):
        addr = ('', self.config.server.port)
        server = SocketServer.ThreadingTCPServer(addr, ServiceHandler)
        server.daemon_threads = True
        server.madcow = self
        while True:
            if select.select([server.socket], [], [], 0.25)[0]:
                server.handle_request()

    def start(self):
        pass

    def output(self, message, req):
        pass

    def botName(self):
        return 'madcow'

    def loadModules(self):
        """
        Dynamic loading of module extensions. This looks for .py files in
        The module directory. They must be well-formed (based on template.py).
        If there are any problems loading, it will skip them instead of crashing.
        """
        try:
            disabled = re.split('\s*[,;]\s*', self.config.modules.disabled)
        except:
            disabled = []

        files = os.walk(self.moduleDir).next()[2]
        logging.info('[MOD] * Reading modules from %s' % self.moduleDir)

        for file in files:
            if file.endswith('.py') is False:
                continue

            modName = file[:-3]
            if modName in self.ignoreModules:
                continue

            if modName == 'ircadmin' and self.config.main.module not in ['irc', 'silcplugin']:
                logging.warn('[MOD] Disabling admin module: for IRC or SILC only')
                continue

            if modName in disabled:
                logging.warn('[MOD] Skipping %s because it is disabled in config' % modName)
                continue

            try:
                module = __import__('modules.' + modName, globals(), locals(), ['MatchObject'])
                MatchObject = getattr(module, 'MatchObject')
                obj = MatchObject(config=self.config, ns=self.ns, dir=self.dir)

                if obj.enabled is False:
                    raise Exception, 'disabled'

                if hasattr(obj, 'help') and obj.help is not None:
                    self.usageLines += obj.help.splitlines()

                logging.info('[MOD] Loaded module %s' % modName)
                self.modules[modName] = obj

                try:
                    Admin = getattr(module, 'Admin')
                    obj = Admin()
                    logging.info('[MOD] Registering Admin functions for %s' % modName)
                    self.admin.modules[modName] = obj
                except:
                    pass

            except Exception, e:
                logging.warn("[MOD] WARN: Couldn't load module %s: %s" % (modName, e))

    def checkAddressing(self, req):
        """
        Pre-processing filter that catches whether the bot is being addressed or not
        """
        nick = self.botName()

        # compile regex based on current nick
        self.reCorrection = re.compile('^\s*no,?\s*%s\s*[,:> -]+\s*(.+)' % re.escape(nick), re.I)
        self.reAddressed = re.compile('^\s*%s\s*[,:> -]+\s*(.+)' % re.escape(nick), re.I)
        self.reFeedback = re.compile('^\s*%s\s*\?+$' % re.escape(nick), re.I)

        # correction: "no, bot, foo is bar"
        try:
            req.message = self.reCorrection.search(req.message).group(1)
            req.correction = True
            req.addressed = True
        except:
            pass

        # bot ping: "bot?"
        if self.reFeedback.search(req.message):
            req.feedback = True

        # addressed
        try:
            req.message = self.reAddressed.search(req.message).group(1)
            req.addressed = True
        except:
            pass

    def log(self, req):
        """
        Logs public chatter
        """
        line = '%s <%s> %s\n' % (time.strftime('%T'), req.nick, req.message)
        file = '%s/logs/%s-irc-%s-%s' % (self.dir, self.ns, req.channel, time.strftime('%F'))

        try:
            fi = open(file, 'a')
            fi.write(line)
        finally:
            fi.close()

    def usage(self):
        """
        Returns help data as a string
        """
        return '\n'.join(self.usageLines)

    def processMessage(self, req):
        """
        Process requests
        """
        if self.config.main.log is True and req.private is False:
            self.log(req)

        if req.nick.lower() in self.ignoreList:
            logging.info('Ignored "%s" from %s' % (req.message, req.nick))
            return

        if req.feedback is True:
            self.output('yes?', req)
            return

        if req.addressed is True and req.message.lower() == 'help':
            self.output(self.usage(), req)
            return

        # pass through admin
        if req.private is True:
            response = self.admin.parse(req)
            if response is not None:
                self.output(response, req)
                return

        for module in self.modules.values():
            if module.requireAddressing and not req.addressed:
                continue

            try:
                args = module.pattern.search(req.message).groups()
            except:
                continue

            # make new dict explictly for thread safety
            kwargs = dict(req.__dict__.items() + [('args', args), ('module', module), ('req', req)])

            if self.allowThreading and module.thread:
                threading.Thread(target=self.processThread, kwargs=kwargs).start()
            else:
                try:
                    response = module.response(**kwargs)
                except Exception, e:
                    logging.warn('UNCAUGHT EXCEPTION')
                    logging.exception(e)
                    response = 'YOU BROKE MADCOW: %s' % str(e)
                if response is not None and len(response) > 0:
                    self.output(response, req)

    def processThread(self, **kwargs):
        try:
            response = kwargs['module'].response(**kwargs)
        except Exception, e:
            logging.warn('UNCAUGHT EXCEPTION')
            logging.exception(e)
            response = 'YOU BROKE MADCOW: %s' % str(e)
        if response is not None and len(response) > 0:
            self.outputLock.acquire()
            self.output(response, kwargs['req'])
            self.outputLock.release()


class Config(object):
    """
    Class to handle configuration directives. Usage is: config.module.attribute
    module maps to the headers in the configuration file. It automatically
    translates floats and integers to the appropriate type.
    """

    isInt = re.compile('^[0-9]+$')
    isFloat = re.compile('^\d+\.\d+$')
    isTrue = re.compile('^\s*(true|yes|on|1)\s*$')
    isFalse = re.compile('^\s*(false|no|off|0)\s*$')

    def __init__(self, file=None, section=None, opts=None):
        if file is not None:
            cfg = ConfigParser()
            cfg.read(file)

            for section in cfg.sections():
                obj = Config(section=section, opts=cfg.items(section))
                setattr(self, section, obj)

        else:
            for key, val in opts:
                if Config.isInt.search(val):
                    val = int(val)
                elif Config.isFloat.search(val):
                    val = float(val)
                elif Config.isTrue.search(val):
                    val = True
                elif Config.isFalse.search(val):
                    val = False

                setattr(self, key, val)

    def __getattr__(self, attr):
        try:
            return getattr(self, attr)
        except:
            try:
                return getattr(self, attr.lower())
            except:
                return None


def detach():
    """
    Daemonize on POSIX system
    """
    if os.name != 'posix': return
    if os.fork() > 0: sys.exit(0)
    os.setsid()
    if os.fork() > 0: sys.exit(0)
    for fd in sys.stdout, sys.stderr: fd.flush()
    si = file('/dev/null', 'r')
    so = file('/dev/null', 'a+')
    se = file('/dev/null', 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    logging.shutdown()

def main():
    """
    Entry point to set up bot and run it
    """

    # where we are being run from
    dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    sys.path.append(dir)

    # parse commandline options
    parser = OptionParser(version=__version__)
    parser.add_option('-c', '--config', default=dir+'/madcow.ini', help='default: %default', metavar='FILE')
    parser.add_option('-d', '--detach', action='store_true', default=False, help='detach when run')
    parser.add_option('-p', '--protocol', help='force the use of this output protocol')
    parser.add_option('-v', '--verbose', action='store_true', default=False, help='turn on verbose output')
    parser.add_option('-D', '--debug', action='store_true', default=False, help='turn on debugging output')
    opts, args = parser.parse_args()

    # logging facility
    logging.basicConfig(level=logging.WARN, format='[%(asctime)s] %(levelname)s: %(message)s')
    if opts.debug:
        logging.root.setLevel(logging.DEBUG)
    elif opts.verbose:
        logging.root.setLevel(logging.INFO)

    # read config file
    config = Config(file=opts.config)

    # load specified protocol
    if opts.protocol:
        protocol = opts.protocol
        config.main.module = protocol
    else:
        protocol = config.main.module

    # dynamic load protocol handler
    try:
        module = __import__('protocols.' + protocol, globals(), locals(), ['ProtocolHandler'])
        ProtocolHandler = getattr(module, 'ProtocolHandler')
    except Exception, e:
        logging.exception(e)
        return 1

    # daemonize if requested
    if config.main.detach or opts.detach:
        detach()

    # run bot
    ProtocolHandler(config=config, dir=dir).start()

    return 0

if __name__ == '__main__':
    sys.exit(main())
