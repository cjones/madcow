#!/usr/bin/env python

"""Madcow infobot"""

import sys
import os
from ConfigParser import ConfigParser
from optparse import OptionParser
import re
import time
import logging as log
from include.authlib import AuthLib
from include.utils import Base, Error
import SocketServer
import select
from signal import signal, SIGHUP, SIGTERM
import shutil
from include.thread import lock, launch_thread, stop_threads

__version__ = '1.1.9'
__author__ = 'Christopher Jones <cjones@gruntle.org>'
__copyright__ = 'Copyright (C) 2007-2008 Christopher Jones'
__license__ = 'GPL'
__all__ = ['Request', 'User', 'Admin', 'ServiceHandler', 'PeriodicEvents',
        'Madcow', 'Config']
_logformat = '[%(asctime)s] %(levelname)s: %(message)s'
_loglevel = log.WARN
_charset = 'latin1'
_pidfile = 'madcow.pid'
_config = 'madcow.ini'
_config_warning = 'created config %s - you should edit this and rerun'

class FileNotFound(Error):
    """Raised when a file is not found"""


class Request(Base):
    """Generic object passed in from protocol handlers for processing"""

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


class User(Base):
    """This class represents a logged in user"""

    def __init__(self, user, flags):
        self.user = user
        self.flags = flags
        self.loggedIn = int(time.time())

    def isAdmin(self):
        """Boolean: user is an admin"""
        return 'a' in self.flags

    def isRegistered(self):
        """Boolean: user is registerd"""
        if 'a' in self.flags or 'r' in self.flags:
            return True
        else:
            return False


class Admin(Base):
    """Class to handle admin interface"""

    _reAdminCommand = re.compile(r'^\s*admin\s+(.+?)\s*$', re.I)
    _reRegister = re.compile('^\s*register\s+(\S+)\s*$', re.I)
    _reAuth = re.compile('^\s*(?:log[io]n|auth)\s+(\S+)\s*$', re.I)
    _reFist = re.compile('^\s*fist\s+(\S+)\s+(.+)$', re.I)
    _reHelp = re.compile('^\s*help\s*$', re.I)
    _reLogout = re.compile('^\s*log(?:out|off)\s*$', re.I)
    _reDelUser = re.compile(r'\s*del(?:ete)?\s+(\S+)\s*$', re.I)
    _reListUsers = re.compile(r'\s*list\s+users\s*$', re.I)
    _reChFlag = re.compile(r'\s*chflag\s+(\S+)\s+(\S+)\s*$', re.I)
    _reAddUser = re.compile(r'^\s*add\s+(\S+)\s+(\S+)(?:\s+(\S+))?\s*$', re.I)

    _basic_usage = [
        'help - this screen',
        'register <pass> - register with bot',
        'login <pass> - login to bot',
    ]

    _loggedin_usage = [
        'logout - log out of bot',
    ]

    _admin_usage = [
        'fist <chan> <msg> - make bot say something in channel',
        'add <user> <flags> [pass] - add a user (no pass = no login)',
        'del <user> - delete a user',
        'list users - list users :P',
        'chflag <user> <[+-][aor]> - update user flags',
    ]

    def __init__(self, bot):
        self.bot = bot
        self.authlib = AuthLib('%s/data/db-%s-passwd' % (bot.dir, bot.ns))
        self.users = {}

    def parse(self, req):
        """Parse request for admin commands and execute, returns output"""
        if not self.bot.config.admin.enabled:
            return
        try:
            command = self._reAdminCommand.search(req.message).group(1)
        except:
            return
        nick = req.nick.lower()

        # register
        try:
            passwd = self._reRegister.search(command).group(1)
            return self.registerUser(nick, passwd)
        except:
            pass

        # log in
        try:
            passwd = self._reAuth.search(command).group(1)
            return self.authenticateUser(nick, passwd)
        except:
            pass

        # help
        help = []
        help += self._basic_usage
        if nick in self.users:
            help += self._loggedin_usage
            if self.users[nick].isAdmin():
                help += self._admin_usage
        if self._reHelp.search(command):
            return '\n'.join(help)

        # don't pass this point unless we are logged in
        try:
            user = self.users[nick]
        except:
            return

        # logout
        if Admin._reLogout.search(command):
            del self.users[nick]
            return 'You are now logged out.'

        # functions past here require admin
        if not user.isAdmin():
            return

        try:
            adduser = self._reAddUser.search(command).groups()
            return self.addUser(*adduser)
        except:
            pass

        # be the puppetmaster
        try:
            channel, message = Admin._reFist.search(command).groups()
            req.sendTo = channel
            return message
        except:
            pass

        # delete a user
        try:
            deluser = self._reDelUser.search(command).group(1)
            self.authlib.delete_user(deluser)
            if self.users.has_key(deluser):
                del self.users[deluser]
            return 'User deleted: %s' % deluser
        except:
            pass

        # list users
        try:
            if self._reListUsers.search(command):
                output = []
                passwd = self.authlib.get_passwd()
                for luser, data in passwd.items():
                    flags = []
                    if 'a' in data['flags']:
                        flags.append('admin')
                    if 'r' in data['flags']:
                        flags.append('registered')
                    if 'o' in data['flags']:
                        flags.append('autoop')
                    if self.users.has_key(luser):
                        flags.append('loggedin')
                    flags = ' '.join(flags)
                    output.append('%s: %s' % (luser, flags))
                return '\n'.join(output)
        except:
            pass

        # update user flags
        try:
            chuser, newflags = self._reChFlag.search(command).groups()
            return self.changeFlags(chuser, newflags)
        except:
            pass

    def changeFlags(self, user, chflags):
        """Change flags for a user"""
        curflags = self.authlib.get_flags(user)
        curflags = set(curflags)
        args = re.split(r'([+-])', chflags)[1:]
        for i in range(0, len(args), 2):
            action, flags = args[i], args[i+1]
            flags = set(flags)
            if action == '-':
                for flag in flags:
                    curflags.discard(flag)
            elif action == '+':
                for flag in flags:
                    curflags.add(flag)
        curflags = ''.join(curflags)
        self.authlib.change_flags(user, curflags)
        if self.users.has_key(user):
            self.users[user].flags = curflags
        return 'flags for %s changed to %s' % (user, curflags)

    def addUser(self, user, flags, password):
        """Add a new user"""
        if self.authlib.user_exists(user):
            return "User already registered."
        flags = ''.join(set(flags))
        self.authlib.add_user(user, password, flags)
        return 'user added: %s' % user

    def registerUser(self, user, passwd):
        """Register with the bot"""
        if not self.bot.config.admin.allowRegistration:
            return "Registration is disabled."
        if self.authlib.user_exists(user):
            return "User already registered."
        flags = self.bot.config.admin.defaultFlags
        if not flags:
            flags = 'r'
        flags = set(flags)
        if user.lower() == self.bot.config.main.owner.lower():
            flags.add('a')
        flags = ''.join(flags)
        self.authlib.add_user(user, passwd, flags)
        return "You are now registered, try logging in: login <pass>"

    def authenticateUser(self, user, passwd):
        """Attempt to log in"""
        if not self.authlib.user_exists(user):
            return "You are not registered: try register <password>."
        if not self.authlib.check_user(user, passwd):
            return 'Nice try.. notifying FBI'
        self.users[user] = User(user, self.authlib.get_flags(user))
        return 'You are now logged in. Message me "admin help" for help'


class GatewayService(Base):
    """Gateway service spawns TCP socket and listens for requests"""

    def __init__(self, madcow):
        addr = (madcow.config.gateway.bind, madcow.config.gateway.port)
        self.server = SocketServer.ThreadingTCPServer(addr, ServiceHandler)
        self.server.daemon_threads = True
        self.server.madcow = madcow

    def start(self):
        """While bot is alive, listen for connections"""
        while self.server.madcow.running:
            if select.select([self.server.socket], [], [], 0.25)[0]:
                self.server.handle_request()


class ServiceHandler(SocketServer.BaseRequestHandler):
    """This class handles the listener service for message injection"""

    # pre-compiled regex
    re_from = re.compile(r'^from:\s*(.+?)\s*$', re.I)
    re_to = re.compile(r'^to:\s*(#\S+)\s*$', re.I)
    re_message = re.compile(r'^message:\s*(.+?)\s*$', re.I)

    def setup(self):
        log.info('connection from %s' % repr(self.client_address))

    def handle(self):
        """Handles a TCP connection to gateway service"""
        data = ''
        while self.server.madcow.running:
            read = self.request.recv(1024)
            if len(read) == 0:
                break
            data += read
        log.info('got payload: %s' % repr(data))

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
            log.warn('invalid payload')
            return

        # see if we can reverse lookup sender
        modules = self.server.madcow.modules.dict()
        db = modules['learn'].get_db('email')
        for user, email in db.items():
            if sent_from == email:
                sent_from = user
                break

        req = Request()
        req.colorize = False
        req.sendTo = send_to
        output = 'message from %s: %s' % (sent_from, message)
        self.server.madcow.output(output, req)

    def finish(self):
        log.info('connection closed by %s' % repr(self.client_address))


class PeriodicEvents(Base):
    """Class to manage modules which are periodically executed"""
    _re_delim = re.compile(r'\s*[,;]\s*')
    _ignore_modules = ['__init__', 'template']
    _process_frequency = 1

    def __init__(self, madcow):
        self.madcow = madcow
        self.last_run = dict.fromkeys(self.madcow.periodics.dict().keys(),
                time.time())

    def start(self):
        """While bot is alive, process periodic event queue"""
        while self.madcow.running:
            self.process_queue()
            time.sleep(self._process_frequency)

    def process_queue(self):
        """Process queue"""
        now = time.time()
        for mod_name, obj in self.madcow.periodics.dict().items():
            if (now - self.last_run[mod_name]) < obj.frequency:
                continue
            self.last_run[mod_name] = now
            launch_thread(target=self.process_thread, name='PeriodicEvent',
                    kwargs={'mod_name': mod_name, 'obj': obj})

    def process_thread(self, **kwargs):
        """Handles a periodic event"""
        try:
            obj = kwargs['obj']
            response = obj.process()
        except Exception, e:
            log.warn('UNCAUGHT EXCEPTION IN %s' % kwargs['mod_name'])
            log.exception(e)
        if response is not None and len(response):
            req = Request()
            req.colorize = False
            req.sendTo = obj.output
            self.madcow.output(response, req)


class Modules(Base):
    _entry = 'Main'
    _pyext = re.compile(r'\.py$')
    _ignore_mods = ('__init__', 'template')

    def __init__(self, madcow, subdir, entry=_entry):
        self.madcow = madcow
        self.subdir = subdir
        self.entry = entry
        self.prefix = os.path.dirname(__file__)
        self.mod_dir = os.path.join(self.prefix, self.subdir)
        self.modules = {}
        self.help = []
        self.load_modules()

    def load_modules(self):
        """Load/reload modules"""
        disabled = list(self._ignore_mods)
        for mod_name, enabled in self.madcow.config.modules.settings.items():
            if not enabled:
                disabled.append(mod_name)
        log.info('reading modules from %s' % self.mod_dir)
        try:
            filenames = os.walk(self.mod_dir).next()[2]
        except Exception, e:
            log.warn("Couldn't load modules from %s: %s" % (self.mod_dir, e))
            return
        for filename in filenames:
            if not self._pyext.search(filename):
                continue
            mod_name = self._pyext.sub('', filename)
            if mod_name in disabled:
                log.info('skipping %s: disabled' % mod_name)
                continue
            if self.modules.has_key(mod_name):
                mod = self.modules[mod_name]['mod']
                try:
                    reload(mod)
                    log.info('reloaded module %s' % mod_name)
                except Exception, e:
                    log.warn("couldn't reload %s: %s" % (mod_name, e))
                    del self.modules[mod_name]
                    continue
            else:
                try:
                    mod = __import__(
                        '%s.%s' % (self.subdir, mod_name),
                        globals(),
                        locals(),
                        [self.entry],
                    )
                except Exception, e:
                    log.warn("couldn't load module %s: %s" % (mod_name, e))
                    continue
                self.modules[mod_name] = {'mod': mod}
            try:
                Main = getattr(mod, self.entry)
                obj = Main(self.madcow)
            except Exception, e:
                log.warn("failure loading %s: %s" % (mod_name, e))
                del self.modules[mod_name]
                continue
            if not obj.enabled:
                log.info("skipped loading %s: disabled" % mod_name)
                del self.modules[mod_name]
                continue
            try:
                if obj.help:
                    self.help.append(obj.help)
                else:
                    raise Exception
            except:
                log.info('no help for module: %s' % mod_name)
            self.modules[mod_name]['obj'] = obj
            log.info('loaded module: %s' % mod_name)

        # if debug level set, show execution order/details of modules
        if log.root.level <= log.DEBUG:
            try:
                for mod_name, obj in self.by_priority():
                    try:
                        log.debug('%-13s: pri=%3s thread=%-5s stop=%s' % (
                            mod_name, obj.priority, obj.allow_threading,
                            obj.terminate))
                    except:
                        pass
            except:
                pass

    def by_priority(self):
        """Return list of tuples for modules, sorted by priority"""
        modules = self.dict()
        modules = sorted(modules.items(), lambda x, y: cmp(x[1].priority,
            y[1].priority))
        return modules

    def dict(self):
        """Return dict of modules"""
        modules = {}
        for mod_name, mod_data in self.modules.items():
            modules[mod_name] = mod_data['obj']
        return modules

    def __iter__(self):
        return self.dict().iteritems()


class Madcow(Base):
    """Core bot handler"""
    reDelim = re.compile(r'\s*[,;]\s*')
    _codecs = ('ascii', 'utf8', 'latin1',)

    def __init__(self, config=None, dir=None):
        """Initialize bot"""
        self.config = config
        self.dir = dir

        self.ns = self.config.modules.dbnamespace

        if self.config.main.ignorelist is not None:
            self.ignoreList = self.config.main.ignorelist
            self.ignoreList = self.reDelim.split(self.ignoreList)
            self.ignoreList = [nick.lower() for nick in self.ignoreList]
            log.info('Ignoring nicks: %s' % ', '.join(self.ignoreList))
        else:
            self.ignoreList = []

        self.admin = Admin(self)

        # set encoding
        if self.config.main.charset:
            self.charset = self.config.main.charset
        else:
            self.charset = _charset

        # load modules
        self.modules = Modules(self, 'modules')
        self.periodics = Modules(self, 'periodic')
        self.usageLines = self.modules.help + self.periodics.help

        # signal handlers
        signal(SIGHUP, self.signal_handler)
        signal(SIGTERM, self.signal_handler)

        self.running = False

    def reload_modules(self):
        """Reload all modules"""
        log.info('reloading modules')
        self.modules.load_modules()
        self.periodics.load_modules()

    def signal_handler(self, sig, frame):
        """Handles signals"""
        if sig == SIGTERM:
            log.warn('got SIGTERM, signaling shutting down')
            self.running = False
        elif sig == SIGHUP:
            self.reload_modules()

    def startGatewayService(self):
        GatewayService(madcow=self).start()

    def startPeriodicService(self, *args, **kwargs):
        PeriodicEvents(madcow=self).start()

    def start(self):
        """Start the bot"""
        self.running = True

        # start local service for handling email gateway
        if self.config.gateway.enabled:
            log.info('launching gateway service')
            launch_thread(self.startGatewayService, 'GatewayService')

        # start thread to handle periodic events
        log.info('launching periodic service')
        launch_thread(self.startPeriodicService, 'PeriodicService')
        self._start()

    def _start(self):
        pass

    def stop(self):
        """Stop the bot"""

        # signal loops in threads that they should exit
        self.running = False

        # protocol specific shutdown procedure (quit irc, etc)
        self._stop()

        # stop all threads
        stop_threads()

    def _stop(self):
        """Protocol-specific shutdown procedure"""
        pass

    def encode(self, text):
        """Force output to the bots encoding"""
        if isinstance(text, str):
            for charset in self._codecs:
                try:
                    text = unicode(text, charset)
                    break
                except:
                    pass

            if isinstance(text, str):
                text = unicode(text, 'ascii', 'replace')
        try:
            text = text.encode(self.charset)
        except:
            text = text.encode('ascii', 'replace')
        return text

    def output(self, *args, **kwargs):
        try:
            if not isinstance(args, list):
                args = list(args)
            args[0] = self.encode(args[0])
            lock.acquire()
            self._output(*args, **kwargs)
        except Exception, e:
            log.error('CRITICAL ERROR IN OUTPUT: %s' % repr(args[0]))
            log.exception(e)

        try:
            lock.release()
        except:
            pass

    def _output(self, message, req=None):
        pass

    def botName(self):
        return 'madcow'

    def checkAddressing(self, req):
        """Is bot being addressed?"""
        nick = self.botName()

        # compile regex based on current nick
        self.reCorrection = re.compile('^\s*no,?\s*%s\s*[,:> -]+\s*(.+)' % 
                re.escape(nick), re.I)
        self.reAddressed = re.compile('^\s*%s\s*[,:> -]+\s*(.+)' %
                re.escape(nick), re.I)
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

    def logpublic(self, req):
        """Logs public chatter"""
        line = '%s <%s> %s\n' % (time.strftime('%T'), req.nick, req.message)
        path = os.path.join(self.dir, 'logs', '%s-irc-%s-%s' % (self.ns,
            req.channel, time.strftime('%F')))

        fo = open(path, 'a')
        try:
            fo.write(line)
        finally:
            fo.close()

    def usage(self):
        """Returns help data as a string"""
        return '\n'.join(sorted(self.usageLines))

    def processMessage(self, req):
        if 'NOBOT' in req.message:
            return

        """Process requests"""
        if self.config.main.logpublic and not req.private:
            self.logpublic(req)

        if req.nick.lower() in self.ignoreList:
            log.info('Ignored "%s" from %s' % (req.message, req.nick))
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
            if response is not None and len(response):
                self.output(response, req)
                return

        if self.config.main.module == 'cli' and req.message == 'reload':
            self.reload_modules()

        for mod_name, mod in self.modules.by_priority():
            log.debug('trying: %s' % mod_name)

            if mod.require_addressing and not req.addressed:
                continue

            try:
                args = mod.pattern.search(req.message).groups()
            except:
                continue

            req.matched = True # module can set this to false to avoid term

            # make new dict explictly for thread safety. XXX hack
            kwargs = dict(req.__dict__.items() + [('args', args),
                ('module', mod), ('req', req)])

            if self.config.main.module == 'cli' or not mod.allow_threading:
                log.debug('running non-threaded code for module %s' % mod_name)
                self.processThread(**kwargs)
            else:
                log.debug('launching thread for module: %s' % mod_name)
                launch_thread(self.processThread, mod_name, kwargs=kwargs)

            if mod.terminate and req.matched:
                log.debug('terminating because %s matched' % mod_name)
                break

    def processThread(self, **kwargs):
        try:
            response = kwargs['module'].response(**kwargs)
        except Exception, e:
            log.warn('UNCAUGHT EXCEPTION')
            log.exception(e)
            response = str(e)
        if response is not None and len(response) > 0:
            self.output(response, kwargs['req'])


class Config(Base):

    class ConfigSection(Base):
        _isint = re.compile(r'^-?[0-9]+$')
        _isfloat = re.compile(r'^-?\d+\.\d+$')
        _istrue = re.compile('^(?:true|yes|on|1)$', re.I)
        _isfalse = re.compile('^(?:false|no|off|0)$', re.I)

        def __init__(self, settings=[]):
            self.settings = {}
            for key, val in settings:
                if self._isint.search(val):
                    val = int(val)
                elif self._isfloat.search(val):
                    val = float(val)
                elif self._istrue.search(val):
                    val = True
                elif self._isfalse.search(val):
                    val = False
                self.settings[key.lower()] = val

        def __getattr__(self, attr):
            attr = attr.lower()
            if self.settings.has_key(attr):
                return self.settings[attr]
            else:
                return None


    def __init__(self, filename):
        if not os.path.exists(filename):
            raise FileNotFound, filename
        parser = ConfigParser()
        parser.read(filename)
        self.sections = {'DEFAULT': self.ConfigSection()}
        for name in parser.sections():
            self.sections[name] = self.ConfigSection(parser.items(name))

    def __getattr__(self, attr):
        attr = attr.lower()
        if self.sections.has_key(attr):
            return self.sections[attr]
        else:
            return self.sections['DEFAULT']


def detach():
    """Daemonize on POSIX system"""
    if os.name != 'posix':
        return
    stop_logging('StreamHandler') # kind of pointless if we're daemonized
    if os.fork() != 0:
        sys.exit(0)
    os.setsid()
    if os.fork() != 0:
        sys.exit(0)
    for fd in sys.stdout, sys.stderr:
        fd.flush()
    si = file('/dev/null', 'r')
    so = file('/dev/null', 'a+')
    se = file('/dev/null', 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    log.info('madcow is launched as a daemon')

def stop_logging(handler_name):
    """
    Stops a specified logging handler by name (e.g. StreamHandler), why
    there's no way to do this in the logging class I do not know.
    """
    logger = log.getLogger('')
    for handler in logger.handlers:
        if handler.__class__.__name__ == handler_name:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)
    log.info('stopped logging to console')

def main():
    """Entry point to set up bot and run it"""

    # where we are being run from
    dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(dir)
    default_config = os.path.join(dir, _config)
    default_pidfile = os.path.join(dir, _pidfile)

    # parse commandline options
    parser = OptionParser(version=__version__)
    parser.add_option('-c', '--config', default=default_config,
            help='default: %default', metavar='FILE')
    parser.add_option('-d', '--detach', action='store_true', default=False,
            help='detach when run')
    parser.add_option('-p', '--protocol',
            help='force the use of this output protocol')
    parser.add_option('-D', '--debug', dest='loglevel', action='store_const',
            const=log.DEBUG,help='turn on debugging output')
    parser.add_option('-v', '--verbose', dest='loglevel', action='store_const',
            const=log.INFO, help='increase logging output')
    parser.add_option('-q', '--quiet', dest='loglevel', action='store_const',
            const=log.WARN, help='only show errors')
    parser.add_option('-P', '--pidfile', default=default_pidfile,
            metavar='<file>', help='default: %default')
    opts, args = parser.parse_args()

    # read config file
    if not os.path.exists(opts.config):
        if opts.config == default_config:
            shutil.copyfile(default_config + '-sample', opts.config)
            print >> sys.stderr, _config_warning % _config
        else:
            print >> sys.stderr, 'config not found: %s' % opts.config
            return 1

    try:
        config = Config(opts.config)
    except FileNotFound:
        sys.stderr.write('config file not found, see README\n')
        return 1
    except Exception, e:
        sys.stderr.write('error parsing config: %s\n' % e)
        return 1

    # init log facility
    try:
        loglevel = getattr(log, config.main.loglevel)
    except:
        loglevel = _loglevel
    if opts.loglevel is not None:
        loglevel = opts.loglevel
    log.basicConfig(level=loglevel, format=_logformat)

    # if specified, log to file as well
    try:
        logfile = config.main.logfile
        if logfile is not None and len(logfile):
            handler = log.FileHandler(filename=logfile)
            handler.setLevel(opts.loglevel)
            formatter = log.Formatter(_logformat)
            handler.setFormatter(formatter)
            log.getLogger('').addHandler(handler)
    except Exception, e:
        log.warn('unable to log to file: %s' % e)
        log.exception(e)

    # load specified protocol
    if opts.protocol:
        protocol = opts.protocol
        config.main.module = protocol
    else:
        protocol = config.main.module

    # dynamic load protocol handler
    try:
        module = __import__('protocols.' + protocol, globals(), locals(),
                ['ProtocolHandler'])
        ProtocolHandler = getattr(module, 'ProtocolHandler')
    except Exception, e:
        log.exception(e)
        return 1

    # daemonize if requested
    if config.main.detach or opts.detach:
        detach()
    
    # write pidfile
    if os.path.exists(opts.pidfile):
        log.warn('removing stale pidfile: %s' % opts.pidfile)
        os.remove(opts.pidfile)
    try:
        fo = open(opts.pidfile, 'wb')
        try:
            fo.write(str(os.getpid()))
        finally:
            fo.close()
    except Exception, e:
        log.warn('filed to write %s: %s' % (opts.pidfile, e))

    # run bot & shut down threads when done
    try:
        bot = ProtocolHandler(config=config, dir=dir)
        bot.start()
    finally:
        log.info('removing pidfile')
        if os.path.exists(opts.pidfile):
            os.remove(opts.pidfile)
        bot.stop()

    log.info('madcow is exiting cleanly')
    return 0

if __name__ == '__main__':
    sys.exit(main())
