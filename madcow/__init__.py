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

"""Core Madcow infobot"""

import threading
import warnings
import shutil
import codecs
import Queue as queue
import time
import sys
import os
import re

# be mindful of win32
try:
    import signal
except ImportError:
    signal = None

# add our include path for third party libs
PREFIX = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PREFIX, 'include'))

from madcow.util import gateway
from madcow.settings import Config

VERSION = 1, 7, 0

__version__ = '.'.join(str(_) for _ in VERSION)
__author__ = 'Chris Jones <cjones@gruntle.org>'
__url__ = 'http://code.google.com/p/madcow/'

delim_re = re.compile(r'\s*[,;]\s*')

class MadcowError(Exception):

    pass


class Madcow(object):

    """Core bot handler, subclassed by protocols"""

    _botname = u'madcow'
    _cor1_re = None
    _cor2_re = None
    _addrend_re = None
    _feedback_re = None
    _addrpre_re = None
    _punc = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    ### INITIALIZATION FUNCTIONS ###

    def __init__(self, config, prefix, scheme=None):
        """Initialize bot"""
        self.colorlib = ColorLib(scheme)
        self.config = config
        self.prefix = prefix
        self.cached_nick = None
        self.namespace = self.config.modules.dbnamespace
        self.running = False

        # parse ignore list
        if self.config.main.ignorelist is not None:
            self.ignore_list = self.config.main.ignorelist
            self.ignore_list = delim_re.split(self.ignore_list)
            self.ignore_list = [nick.lower() for nick in self.ignore_list]
            log.info(u'Ignoring nicks: %s', u', '.join(self.ignore_list))
        else:
            self.ignore_list = []

        # bot aliases
        if self.config.main.aliases:
            self.aliases = delim_re.split(self.config.main.aliases)
        else:
            self.aliases = []

        # set encoding
        self.charset = CHARSET
        if self.config.main.charset:
            try:
                self.charset = codecs.lookup(self.config.main.charset).name
            except LookupError:
                log.warn('unknown charset %s, using default %s',
                         self.config.main.charset, self.charset)

        # create admin instance
        self.admin = Admin(self)

        # load modules
        self.modules = Modules(self, u'modules', self.prefix)
        self.periodics = Modules(self, u'periodic', self.prefix)
        self.usage_lines = self.modules.help + self.periodics.help
        self.usage_lines.append(u'help - this screen')
        self.usage_lines.append(u'version - get bot version')

        # signal handlers
        if SIGNALS:
            signal(SIGHUP, self.signal_handler)
            signal(SIGTERM, self.signal_handler)

        # initialize threads
        self.request_queue = Queue()
        self.response_queue = Queue()
        self.lock = RLock()

    def start(self):
        """Start the bot"""
        self.running = True

        # start services
        for service in Service.__subclasses__():
            log.info('starting service: %s', service.__name__)
            thread = service(self)
            thread.setDaemon(True)
            thread.start()

        # start worker threads
        for i in range(self.config.main.workers):
            name = u'ModuleWorker%d' % (i + 1)
            log.debug('Starting Thread: %s', name)
            thread = threading.Thread(target=self.request_handler, name=name)
            thread.setDaemon(True)
            thread.start()

        self.run()

    def run(self):
        """Runs madcow loop"""
        while self.running:
            self.check_response_queue()
            line = raw_input('>>> ').decode(sys.stdin.encoding, 'replace')
            line = line.rstrip()
            req = Request(message=line)
            req.nick = os.environ['USER']
            req.channel = u'none'
            req.addressed = True
            req.private = True
            self.check_addressing(req)
            self.process_message(req)

    def signal_handler(self, sig, *args):
        """Handles signals"""
        if sig == SIGTERM:
            log.warn(u'got SIGTERM, signaling shutting down')
            self.running = False
        elif sig == SIGHUP:
            self.reload_modules()

    def reload_modules(self):
        """Reload all modules"""
        log.info(u'reloading modules')
        self.modules.load_modules()
        self.periodics.load_modules()

    ### OUTPUT FUNCTIONS

    def output(self, message, req=None):
        """Add response to output queue"""
        self.response_queue.put((message, req))

    def check_response_queue(self):
        """Check if there's any message in response queue and process"""
        try:
            self.handle_response(*self.response_queue.get_nowait())
        except Empty:
            pass
        except Exception, error:
            log.exception(error)

    def handle_response(self, response, req=None):
        """encode output, lock threads, and call protocol_output"""
        try:
            self.lock.acquire()
            try:
                self.protocol_output(response, req)
            except Exception, error:
                log.error('error in output: %r', response)
                log.exception(error)
        finally:
            self.lock.release()

    def protocol_output(self, message, req=None):
        """Override with protocol-specific output method"""
        print message.encode(sys.stdout.encoding, 'replace')

    ### MODULE PROCESSING ###

    def request_handler(self):
        """Dispatcher for workers"""
        while self.running:
            request = self.request_queue.get()
            try:
                self.process_module_item(request)
            except Exception, error:
                log.exception(error)

    def process_module_item(self, request):
        """Run module response method and output any response"""
        obj, nick, args, kwargs = request
        try:
            response = obj.response(nick, args, kwargs)
        except Exception, error:
            log.warn(u'Uncaught module exception')
            log.exception(error)
            return

        if response is not None and len(response) > 0:
            self.output(response, kwargs[u'req'])

    ### INPUT FROM USER ###

    def check_addressing(self, req):
        """Is bot being addressed?"""

        # this is.. torturous.  it works, but it really really
        # needs to be un-perlified at some point.
        botname = self.botname()
        if botname != self.cached_nick:
            self.cached_nick = botname
            nicks = []
            pre_nicks = []
            for nick in [botname] + self.aliases:
                nick_e = re.escape(nick)
                nicks.append(nick_e)
                if nick_e[-1] not in self._punc:
                    nick_e += '[-,: ]+'
                pre_nicks.append(nick_e)
            nicks = '(?:%s)' % '|'.join(nicks)
            pre_nicks = '(?:%s)' % '|'.join(pre_nicks)
            pre_pat = r'^\s*%s\s*(.+)$' % pre_nicks
            self._addrpre_re = re.compile(pre_pat, re.I)
            self._cor1_re = re.compile(
                    r'^\s*no[ ,]+%s[ ,:-]+\s*(.+)$' % nicks, re.I)
            self._cor2_re = re.compile(
                    r'^\s*no[ ,]+(.+)$', re.I)
            self._feedback_re = re.compile(
                    r'^\s*%s[ !]*\?[ !]*$' % nicks, re.I)
            self._addrend_re = re.compile(
                    r'^(.+),\s+%s\W*$' % nicks, re.I)

        if self._feedback_re.search(req.message):
            req.feedback = req.addressed = True

        try:
            req.message = self._addrend_re.search(req.message).group(1)
            req.addressed = True
        except AttributeError:
            pass

        try:
            req.message = self._addrpre_re.search(req.message).group(1)
            req.addressed = True
        except AttributeError:
            pass

        try:
            req.message = self._cor1_re.search(req.message).group(1)
            req.correction = req.addressed = True
        except AttributeError:
            pass

        if req.addressed:
            try:
                req.message = self._cor2_re.search(req.message).group(1)
                req.correction = True
            except AttributeError:
                pass

    def process_message(self, req):
        """Process requests"""
        if u'NOBOT' in req.message:
            return
        if self.config.main.logpublic and not req.private:
            self.logpublic(req)
        if req.nick.lower() in self.ignore_list:
            log.info(u'Ignored %r from %s', req.message, req.nick)
            return
        if req.feedback:
            self.output(u'yes?', req)
            return
        if req.addressed and req.message.lower() == u'help':
            if self.config.main.module == u'irc':
                req.sendto = req.nick
            elif self.config.main.module == u'silcplugin':
                self.lock.acquire()
                try:
                    req.sendto = req.silc_sender
                    req.private = True
                    req.channel = u'privmsg'
                finally:
                    self.lock.release()
            self.output(self.usage(), req)
            return
        if req.addressed and req.message.lower() == u'version':
            res = u'madcow %s by %s: %s' % (__version__, __author__, MADCOW_URL)
            self.output(res, req)
            return
        if req.private:
            response = self.admin.parse(req)
            if response is not None and len(response):
                self.output(response, req)
                return
        if self.config.main.module == u'cli' and req.message == u'reload':
            self.reload_modules()
        for mod_name, mod in self.modules.by_priority():
            obj = mod['obj']
            log.debug('trying: %s', mod_name)
            if obj.require_addressing and not req.addressed:
                continue
            try:
                args = obj.pattern.search(req.message).groups()
            except AttributeError:
                continue

            req.matched = True # module can set this to false to avoid term

            # config forces this to be private
            if mod[u'private']:
                req.private = True
                req.sendto = req.nick

            # see if we can filter some of this information..
            kwargs = {u'req': req}
            kwargs.update(req.__dict__)

            request = (obj, req.nick, args, kwargs,)

            if (self.config.main.module in (u'cli', u'ipython') or
                not obj.allow_threading):
                log.debug('running non-threaded code for module %s', mod_name)
                self.process_module_item(request)
            else:
                log.debug('launching thread for module: %s', mod_name)
                self.request_queue.put(request)

            if obj.terminate and req.matched:
                log.debug('terminating because %s matched', mod_name)
                break

    def logpublic(self, req):
        """Logs public chatter"""
        message = req.message
        if req.action:
            message = u'ACTION: %s' % message
        line = u'%s <%s> %s\n' % (strftime(u'%T'), req.nick, message)
        path = os.path.join(self.prefix, u'logs', u'%s-irc-%s-%s' % (self.namespace, req.channel, strftime(u'%F')))
        logfile = open(path, u'a')
        try:
            logfile.write(line.encode(self.charset, 'replace'))
        finally:
            logfile.close()

    ### MISC FUNCTIONS ###

    def usage(self):
        """Returns help data as a string"""
        return u'\n'.join(sorted(self.usage_lines))

    def stop(self):
        """Stop the bot"""
        self.running = False

    def botname(self):
        """Should return the real name of the bot"""
        return self._botname


class Service(threading.Thread):

    """Service object"""

    def __init__(self, bot):
        self.bot = bot
        super(Service, self).__init__(name=type(self).__name__)


class GatewayService(gateway.GatewayService, Service):

    """Gateway service spawns TCP socket and listens for requests"""


class PeriodicEvents(Service):

    """Class to manage modules which are periodically executed"""

    _ignore_modules = [u'__init__', u'template']
    _process_frequency = 1

    def __init__(self, *args, **kwargs):
        self.last_run = {}
        super(PeriodicEvents, self).__init__(*args, **kwargs)

    def run(self):
        """While bot is alive, process periodic event queue"""
        delay = 5
        now = unix_time()
        for mod_name, mod in self.bot.periodics.modules.iteritems():
            self.last_run[mod_name] = now - mod[u'obj'].frequency + delay

        while self.bot.running:
            self.process_queue()
            sleep(self._process_frequency)

    def process_queue(self):
        """Process queue"""
        now = unix_time()
        for mod_name, mod in self.bot.periodics.modules.iteritems():
            obj = mod[u'obj']
            if (now - self.last_run[mod_name]) < obj.frequency:
                continue
            self.last_run[mod_name] = now
            req = Request()
            req.sendto = obj.output
            request = (obj, None, None, {u'req': req})
            self.bot.request_queue.put(request)


class User(object):

    """This class represents a logged in user"""

    def __init__(self, user, flags):
        self.user = user
        self.flags = flags

    def is_asmin(self):
        """Boolean: user is an admin"""
        return u'a' in self.flags

    def is_registered(self):
        """Boolean: user is registerd"""
        if u'a' in self.flags or u'r' in self.flags:
            return True
        else:
            return False


class Admin(object):

    """Class to handle admin interface"""

    _admin_cmd_re = re.compile(r'^\s*admin\s+(.+?)\s*$', re.I)
    _register_re = re.compile(u'^\s*register\s+(\S+)\s*$', re.I)
    _auth_re = re.compile(u'^\s*(?:log[io]n|auth)\s+(\S+)\s*$', re.I)
    _fist_re = re.compile(u'^\s*fist\s+(\S+)\s+(.+)$', re.I)
    _help_re = re.compile(u'^\s*help\s*$', re.I)
    _logout_re = re.compile(u'^\s*log(?:out|off)\s*$', re.I)
    _deluser_re = re.compile(r'\s*del(?:ete)?\s+(\S+)\s*$', re.I)
    _list_users_re = re.compile(r'\s*list\s+users\s*$', re.I)
    _chflag_re = re.compile(r'\s*chflag\s+(\S+)\s+(\S+)\s*$', re.I)
    _adduser_re = re.compile(r'^\s*add\s+(\S+)\s+(\S+)(?:\s+(\S+))?\s*$', re.I)
    _basic_usage = [u'help - this screen',
                    u'register <pass> - register with bot',
                    u'login <pass> - login to bot']
    _loggedin_usage = [u'logout - log out of bot']
    _admin_usage = [u'fist <chan> <msg> - make bot say something in channel',
                    u'add <user> <flags> [pass] - add a user',
                    u'del <user> - delete a user',
                    u'list users - list users :P',
                    u'chflag <user> <[+-][aor]> - update user flags']

    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.authlib = AuthLib(u'%s/data/db-%s-passwd' % (bot.prefix,
                                                          bot.namespace),
                               bot.charset)

    def parse(self, req):
        """Parse request for admin commands and execute, returns output"""
        if not self.bot.config.admin.enabled:
            return
        try:
            command = self._admin_cmd_re.search(req.message).group(1)
        except AttributeError:
            return
        nick = req.nick.lower()

        # register
        try:
            passwd = self._register_re.search(command).group(1)
            return self.register_user(nick, passwd)
        except AttributeError:
            pass

        # log in
        try:
            passwd = self._auth_re.search(command).group(1)
            return self.authuser(nick, passwd)
        except AttributeError:
            pass

        # help
        usage = []
        usage += self._basic_usage
        if nick in self.users:
            usage += self._loggedin_usage
            if self.users[nick].is_asmin():
                usage += self._admin_usage
        if self._help_re.search(command):
            return u'\n'.join(usage)

        # don't pass this point unless we are logged in
        if nick not in self.users:
            return
        user = self.users[nick]

        # logout
        if Admin._logout_re.search(command):
            del self.users[nick]
            return u'You are now logged out.'

        # functions past here require admin
        if not user.is_asmin():
            return

        try:
            adduser, flags, password = self._adduser_re.search(command).groups()
            return self.adduser(adduser, flags, password)
        except AttributeError:
            pass

        # be the puppetmaster
        try:
            channel, message = Admin._fist_re.search(command).groups()
            req.sendto = channel
            return message
        except AttributeError:
            pass

        # delete a user
        try:
            deluser = self._deluser_re.search(command).group(1)
            self.authlib.delete_user(deluser)
            if deluser in self.users:
                del self.users[deluser]
            return u'User deleted: %s' % deluser
        except AttributeError:
            pass

        # list users
        if self._list_users_re.search(command):
            output = []
            passwd = self.authlib.get_passwd()
            for luser, data in passwd.items():
                flags = []
                if u'a' in data[u'flags']:
                    flags.append(u'admin')
                if u'r' in data[u'flags']:
                    flags.append(u'registered')
                if u'o' in data[u'flags']:
                    flags.append(u'autoop')
                if luser in self.users:
                    flags.append(u'loggedin')
                flags = u' '.join(flags)
                output.append(u'%s: %s' % (luser, flags))
            return u'\n'.join(output)

        # update user flags
        try:
            chuser, newflags = self._chflag_re.search(command).groups()
            return self.change_flags(chuser, newflags)
        except AttributeError:
            pass

    def change_flags(self, user, chflags):
        """Change flags for a user"""
        curflags = self.authlib.get_flags(user)
        curflags = set(curflags)
        args = re.split(r'([+-])', chflags)[1:]
        for i in range(0, len(args), 2):
            action, flags = args[i], args[i+1]
            flags = set(flags)
            if action == u'-':
                for flag in flags:
                    curflags.discard(flag)
            elif action == u'+':
                for flag in flags:
                    curflags.add(flag)
        curflags = u''.join(curflags)
        self.authlib.change_flags(user, curflags)
        if user in self.users:
            self.users[user].flags = curflags
        return u'flags for %s changed to %s' % (user, curflags)

    def adduser(self, user, flags, password):
        """Add a new user"""
        if self.authlib.user_exists(user):
            return u"User already registered."
        flags = u''.join(set(flags))
        self.authlib.add_user(user, password, flags)
        return u'user added: %s' % user

    def register_user(self, user, passwd):
        """Register with the bot"""
        if not self.bot.config.admin.allowRegistration:
            return u"Registration is disabled."
        if self.authlib.user_exists(user):
            return u"User already registered."
        flags = self.bot.config.admin.defaultFlags
        if not flags:
            flags = u'r'
        flags = set(flags)
        if user.lower() == self.bot.config.main.owner.lower():
            flags.add(u'a')
        flags = u''.join(flags)
        self.authlib.add_user(user, passwd, flags)
        return u"You are now registered, try logging in: login <pass>"

    def authuser(self, user, passwd):
        """Attempt to log in"""
        if not self.authlib.user_exists(user):
            return u"You are not registered: try register <password>."
        if not self.authlib.check_user(user, passwd):
            return u'Nice try.. notifying FBI'
        self.users[user] = User(user, self.authlib.get_flags(user))
        return u'You are now logged in. Message me "admin help" for help'


class Modules(object):

    """This class dynamically loads plugins and instantiates them"""

    _pyext = re.compile(r'\.py$')
    _ignore_mods = (u'__init__', u'template')

    def __init__(self, madcow, subdir, prefix):
        self.madcow = madcow
        self.subdir = subdir
        self.mod_dir = os.path.join(prefix, self.subdir)
        self.modules = {}
        self.help = []
        self.load_modules()

    def load_modules(self):
        """Load/reload modules"""
        disabled = list(self._ignore_mods)
        for mod_name, enabled in self.madcow.config.modules:
            if not enabled:
                disabled.append(mod_name)
        private = delim_re.split(self.madcow.config.modules.private)
        log.info('reading modules from %s', self.mod_dir)
        try:
            filenames = os.listdir(self.mod_dir)
        except Exception, error:
            log.warn("Couldn't load modules from %s: %s", self.mod_dir, error)
            log.exception(error)
            return
        for filename in filenames:
            if not self._pyext.search(filename):
                continue
            mod_name = self._pyext.sub(u'', filename)
            if mod_name in disabled:
                log.debug('skipping %s: disabled', mod_name)
                continue
            if mod_name in self.modules:
                mod = self.modules[mod_name][u'mod']
                try:
                    reload(mod)
                    log.debug('reloaded module %s', mod_name)
                except Exception, error:
                    log.warn("couldn't reload %s: %s", mod_name, error)
                    del self.modules[mod_name]
                    continue
            else:
                try:
                    mod = __import__(u'%s.%s' % (self.subdir, mod_name),
                                     globals(), locals(), [u'Main'])
                except Exception, error:
                    log.warn("couldn't load module %s: %s", mod_name, error)
                    continue
                self.modules[mod_name] = {u'mod': mod,
                                          u'private': mod_name in private}
            try:
                obj = mod.Main(self.madcow)
            except Exception, error:
                log.warn("failure loading %s: %s", mod_name, error)
                del self.modules[mod_name]
                continue
            if not obj.enabled:
                log.debug("skipped loading %s: disabled", mod_name)
                del self.modules[mod_name]
                continue
            try:
                if not obj.help:
                    raise AttributeError
                self.help.append(obj.help)
            except AttributeError:
                log.debug('no help for module: %s', mod_name)
            self.modules[mod_name][u'obj'] = obj
            log.debug('loaded module: %s', mod_name)

        # if debug level set, show execution order/details of modules
        if log.root.level <= log.DEBUG:
            try:
                for mod_name, mod in self.by_priority():
                    log.debug('%-13s: pri=%3s thread=%-5s stop=%s',
                              mod_name, obj.priority,
                              obj.allow_threading,
                              obj.terminate)
            except AttributeError:
                pass

    def by_priority(self):
        """Return list of tuples for modules, sorted by priority"""
        return sorted(self.modules.iteritems(),
                      key=lambda item: item[1][u'obj'].priority)


def daemonize():
    """POSIX only: run as a daemon"""
    import resource
    if os.fork():
        os._exit(0)
    os.setsid()
    if os.fork():
        os._exit(0)
    for fd in xrange(resource.getrlimit(resource.RLIMIT_NOFILE)[0]):
        try:
            os.close(fd)
        except OSError:
            pass
    fd = os.open(os.devnull, os.O_RDWR)
    os.dup(fd)
    os.dup(fd)
    os.umask(027)
    os.chdir('/')
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)


def run(base, settings=None):
    """Execute the main bot"""

    # if this is a new bot, create base and stop
    new_bot = False
    for subdir in 'db', 'log':
        dir = os.path.join(base, subdir)
        if not os.path.exists(dir):
            os.makedirs(dir)
            new_bot = True
    settings_file = os.path.join(base, 'settings.ini')
    default_settings_file = os.path.join(PREFIX, 'settings', 'default.ini')
    if not os.path.exists(settings_file):
        shutil.copy(default_settings_file, settings_file)
        os.chmod(settings_file, 0644)
        new_bot = True
    if new_bot:
        raise MadcowError('A new bot has been created at %s, please modify config and rerun' % base)

    config = Config(settings_file, default_settings_file, overrides=settings)
    config.values['main']['logfile'] = 'newlogfile.txt'
    config.save('/home/cjones/wtf.ini')
    print config.main.logfile


def main():
    """Entry point to set up bot and run it"""

    # init log facility
    if opts.loglevel is None:
        try:
            loglevel = log._levelNames[config.main.loglevel.upper()]
        except KeyError:
            loglevel = None
    else:
        loglevel = opts.loglevel
    if loglevel is not None:
        log.root.setLevel(loglevel)

    # load specified protocol
    if opts.protocol:
        protocol = config.main.module = opts.protocol
    else:
        protocol = config.main.module

    # setup global UserAgent
    ua.setup(cookies=config.http.cookies, agent=config.http.agent,
             timeout=config.http.timeout)

    # daemonize if requested, but not when interactive!
    # note: this must happen BEFORE forking, otherwise the pid it
    # records will be incorrect and fuck up any rc scripts.
    if config.main.detach or opts.detach:
        if __name__ != u'__main__':
            log.warn(u'not detaching in interactive shell')
        elif protocol == u'cli':
            log.warn(u'not detaching for commandline client')
        else:
            daemonize()

    # if specified, log to file as well
    if config.main.logfile:
        logfile = config.main.logfile
        if not logfile.startswith('/'):
            logfile = os.path.join(prefix, logfile)
        handler = log.FileHandler(logfile)
        handler.setFormatter(log.root.handlers[0].formatter)
        log.root.addHandler(handler)
        log.info('logging messages to %s', logfile)

    # determine pidfile to use (commandline overrides config)
    if opts.pidfile:
        pidfile = opts.pidfile
    else:
        pidfile = config.main.pidfile

    # write pidfile. from this point on, capture ALL exceptions
    # so that the pidfile can be removed when we're done
    if pidfile:
        if os.path.exists(pidfile):
            log.warn('removing stale pidfile: %s', pidfile)
            os.remove(pidfile)
        try:
            pidfp = open(pidfile, u'wb')
            try:
                pidfp.write(unicode(os.getpid()))
            finally:
                pidfp.close()
        except Exception, error:
            log.warn('failed to write %s: %s', pidfile, error)
            log.exception(error)

    # import protocol handler
    handler = None
    try:
        module = __import__(u'protocols', globals(), locals(), [protocol])
        handler = getattr(module, protocol).ProtocolHandler
    except ImportError, error:
        # give useful error messages for some known failures (*cough* piece
        # of shit SILC *cough*)
        if unicode(error) == u'No module named silc':
            log.error(u'you must install silc-toolkit and pysilc!')
        else:
            try:
                so = re.search(r'Shared object "(libsilc.*?)" not found',
                               unicode(error)).group(1)
                log.error(u'pysilc cannot find silc-toolkit, try setting '
                          u'LD_LIBRARY_PATH to the location of ' + so)
            except AttributeError:
                log.error('error loading protocol %s: %s', protocol, error)
    except AttributeError:
        log.error(u'no handler found for protocol: ' + protocol)
    except Exception, error:
        log.exception(error)

    # try psyco optimization
    if config.main.psyco and protocol != u'ipython':
        try:
            import psyco
            psyco.cannotcompile(re.compile)
            psyco.full()
            log.info(u'psyco full scan complete')
        except ImportError:
            pass

    if handler:
        # actually run bot
        try:
            bot = handler(config, prefix)
            bot.start()
        except Exception, error:
            log.error(u'fatal error in bot, shutting down')
            log.exception(error)

        # this would be in a finally block, but 2.4 compatibility :/
        try:
            bot.stop()
        except Exception, error:
            log.exception(error)

    if pidfile and os.path.exists(pidfile):
        log.info(u'removing pidfile')
        try:
            os.remove(pidfile)
        except Exception, error:
            log.warn('failed to remove pidfile %s', pidfile)
            log.exception(error)

    log.info(u'madcow is shutting down')
    return 0

if __name__ == '__main__':
    sys.exit(main())
