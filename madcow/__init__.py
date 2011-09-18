# Copyright (C) 2007-2011 Christopher Jones
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

from madcow.util import gateway, get_logger, http, Request
from madcow.conf import settings
from madcow.util.color import ColorLib
from madcow.util.auth import AuthLib
from madcow.util.textenc import encode, decode, set_preferred_encoding, get_encoding

VERSION = 2, 2, 0

__version__ = '.'.join(str(_) for _ in VERSION)
__author__ = 'Chris Jones <cjones@gruntle.org>'
__url__ = 'http://code.google.com/p/madcow/'

delim_re = re.compile(r'\s*[,;]\s*')
help_re = re.compile(r'^help(?:\s+(\w+))?$')

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
    _punc = '!"#$%&\'()*+,-./:;<=>?@[\\]^`{|}~'

    ### INITIALIZATION FUNCTIONS ###

    def __init__(self, base, scheme=None):
        """Initialize bot"""
        self.base = base
        self.log = get_logger('madcow', unique=False, stream=sys.stdout)
        self.colorlib = ColorLib(scheme)
        self.cached_nick = None
        self.running = False

        self.ignore_list = [nick.lower() for nick in settings.IGNORE_NICKS]

        # set encoding
        set_preferred_encoding(settings.ENCODING)
        self.log.info('Preferred encoding set to %s', get_encoding())

        # create admin instance
        self.admin = Admin(self)

        # load modules
        self.modules = Modules(self, 'modules', settings.MODULES)
        self.tasks = Modules(self, 'tasks', settings.TASKS)
        self.usage_lines = self.modules.help + self.tasks.help
        self.usage_lines.append(u'help - this screen')
        self.usage_lines.append(u'version - get bot version')

        # signal handlers
        if signal:
            signal.signal(signal.SIGHUP, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

        # initialize threads
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.lock = threading.RLock()
        self.ignore_res = []
        if settings.IGNORE_REGEX:
            for pattern in settings.IGNORE_REGEX:
                try:
                    regex = re.compile(pattern, re.I)
                except Exception, error:
                    self.log.warn('%r pattern did not compile', pattern)
                    continue
                self.ignore_res.append(regex)

    @property
    def prefix(self):
        return PREFIX

    def start(self):
        """Start the bot"""
        self.running = True

        # start services
        for service in Service.__subclasses__():
            self.log.info('starting service: %s', service.__name__)
            thread = service(self)
            thread.setDaemon(True)
            thread.start()

        # start worker threads
        for i in range(settings.WORKERS):
            name = u'ModuleWorker%d' % (i + 1)
            self.log.debug('Starting Thread: %s', name)
            thread = threading.Thread(target=self.request_handler, name=name)
            thread.setDaemon(True)
            thread.start()

        self.run()

    def run(self):
        """Runs madcow loop"""
        while self.running:
            self.check_response_queue()
            line = decode(raw_input('>>> '), sys.stdin.encoding).rstrip()
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
            self.log.warn(u'got SIGTERM, signaling shutting down')
            self.running = False
        elif sig == SIGHUP:
            self.reload_modules()

    def reload_modules(self):
        """Reload all modules"""
        self.log.info(u'reloading modules')
        self.modules.load_modules()
        self.tasks.load_modules()

    ### OUTPUT FUNCTIONS

    def output(self, message, req=None):
        """Add response to output queue"""
        self.response_queue.put((message, req))

    def check_response_queue(self):
        """Check if there's any message in response queue and process"""
        try:
            self.handle_response(*self.response_queue.get_nowait())
        except queue.Empty:
            pass
        except:
            self.log.exception('error reading response queue')

    def handle_response(self, response, req=None):
        """encode output, lock threads, and call protocol_output"""
        with self.lock:
            try:
                self.protocol_output(response, req)
            except:
                self.log.exception('error in output: %r', response)

    def protocol_output(self, message, req=None):
        """Override with protocol-specific output method"""
        print encode(message, sys.stdout.encoding)

    ### MODULE PROCESSING ###

    def request_handler(self):
        """Dispatcher for workers"""
        while self.running:
            request = self.request_queue.get()
            try:
                self.process_module_item(request)
            except:
                self.log.exception('error processing request')

    def process_module_item(self, request):
        """Run module response method and output any response"""
        obj, nick, args, kwargs = request
        try:
            response = obj.get_response(nick, args, kwargs)
        except:
            self.log.exception(u'Uncaught module exception')
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
            for nick in [botname] + settings.ALIASES:
                nick_e = re.escape(nick)
                nicks.append(nick_e)
                if nick_e[-1] not in self._punc:
                    nick_e += '[-,: ]+'
                pre_nicks.append(nick_e)
            nicks = '(?:%s)' % '|'.join(nicks)
            pre_nicks = '(?:%s)' % '|'.join(pre_nicks)
            pre_pat = r'^\s*%s\s*(.+)$' % pre_nicks
            self._addrpre_re = re.compile(pre_pat, re.I)
            self._cor1_re = re.compile(r'^\s*no[ ,]+%s[ ,:-]+\s*(.+)$' % nicks, re.I)
            self._cor2_re = re.compile(r'^\s*no[ ,]+(.+)$', re.I)
            self._feedback_re = re.compile(r'^\s*%s[ !]*\?[ !]*$' % nicks, re.I)
            self._addrend_re = re.compile(r'^(.+),\s+%s\W*$' % nicks, re.I)

        if self._feedback_re.search(req.message):
            req.feedback = req.addressed = True

        try:
            req.message = self._addrend_re.search(req.message).group(1)
            req.addressed = True
        except AttributeError:
            pass

        try:
            req.message = self._addrpre_re.search(req.message).group(1)  # XXX
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
        for ignore_re in self.ignore_res:
            if ignore_re.search(req.message):
                return
        if settings.LOG_PUBLIC and not req.private:
            self.logmessage(req)
        if req.nick.lower() in self.ignore_list:
            self.log.info(u'Ignored %r from %s', req.message, req.nick)
            return

        # builtins
        if req.feedback:
            self.output(u'yes?', req)
            return
        if req.addressed:
            lmessage = req.message.lower().strip()
            help_result = help_re.search(lmessage)
            if help_result is not None:
                if settings.PRIVATE_HELP:
                    req.make_private()
                module = help_result.group(1)
                if module:
                    if module in self.modules.modules:
                        self.output(self.modules.modules[module]['obj'].help, req)
                    elif module == u'all':
                        self.output(self.usage(), req)
                    else:
                        self.output(u'Unknown module %s' % module, req)
                else:
                    self.output(u'usage: help [<module>|all]', req)
                    self.output(u'modules: %s' % u' '.join(sorted(self.modules.modules)), req)
                return
            if lmessage == u'version':
                self.output(u'madcow %s by %s: %s' % (__version__, __author__, __url__), req)
                return
        if req.private:
            response = self.admin.parse(req)
            if response is not None and len(response):
                self.output(response, req)
                return
        if settings.PROTOCOL == u'cli' and req.message == u'reload':
            self.reload_modules()
        for mod_name, mod in self.modules.by_priority():
            obj = mod['obj']
            self.log.debug('trying: %s', mod_name)
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

            if (settings.PROTOCOL in (u'cli', u'ipython') or not obj.allow_threading):
                self.log.debug('running non-threaded code for module %s', mod_name)
                self.process_module_item(request)
            else:
                self.log.debug('launching thread for module: %s', mod_name)
                self.request_queue.put(request)

            if obj.terminate and req.matched:
                self.log.debug('terminating because %s matched', mod_name)
                break

    def logmessage(self, req):
        """Logs public chatter"""
        self.logpublic(req.channel, (u' * %s %s' if req.action else u'<%s> %s') % (req.nick, req.message))

    def logpublic(self, channel, line):
        logdir = os.path.join(self.base, 'log', 'public')
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        filename = ['public', channel.replace('#', '')]
        if settings.LOG_BY_DATE:
            filename.append(time.strftime('%F'))
        logfile = os.path.join(logdir, '-'.join(filename) + '.log')
        with open(logfile, 'a') as fp:
            print >> fp, '%s %s' % (time.strftime('%T'), encode(line))

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
        now = time.time()
        for mod_name, mod in self.bot.tasks.modules.iteritems():
            self.last_run[mod_name] = now - mod[u'obj'].frequency + delay

        while self.bot.running:
            self.process_queue()
            time.sleep(self._process_frequency)

    def process_queue(self):
        """Process queue"""
        now = time.time()
        for mod_name, mod in self.bot.tasks.modules.iteritems():
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
        self.authlib = AuthLib(os.path.join(bot.base, 'db', 'passwd'))

    def parse(self, req):
        """Parse request for admin commands and execute, returns output"""
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
        if not settings.ALLOW_REGISTRATION:
            return u"Registration is disabled."
        if self.authlib.user_exists(user):
            return u"User already registered."
        flags = settings.DEFAULT_FLAGS
        if not flags:
            flags = u'r'
        flags = set(flags)
        if user.lower() == settings.OWNER_NICK.lower():
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

    def __init__(self, madcow, subdir, names):
        self.madcow = madcow
        self.subdir = subdir
        self.names = names
        self.modules = {}
        self.help = []
        self.load_modules()

    def load_modules(self):
        """Load/reload modules"""
        self.madcow.log.info('loading modules')
        for name in self.names:
            try:
                mod = __import__('madcow.' + self.subdir, globals(), locals(), [name])
                mod = getattr(mod, name)
                if not mod.Main.enabled:
                    raise MadcowError('this module is marked as disabled')
                if name in self.modules:
                    reload(mod)
                self.modules[name] = {
                        'mod': mod,
                        'obj': mod.Main(self.madcow),
                        'private': name in settings.PRIVATE_MODULES,
                        }
                help = getattr(self.modules[name]['obj'], 'help', None)
                if help:
                    self.help.append(help)
                self.madcow.log.info('loaded module: %s', name)
            except Exception, error:
                self.madcow.log.warn('failed to load %s: %s', name, error)
                if name in self.modules:
                    del self.modules[name]

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


def run(base):
    """Execute the main bot"""

    # if this is a new bot, create base and stop
    base = os.path.realpath(base)
    for subdir in 'db', 'log':
        dir = os.path.join(base, subdir)
        if not os.path.exists(dir):
            os.makedirs(dir)
    settings_file = os.path.join(base, 'settings.py')
    default_settings_file = os.path.join(PREFIX, 'conf', 'defaults.py')
    if not os.path.exists(settings_file):
        shutil.copy(default_settings_file, settings_file)
        os.chmod(settings_file, 0644)
        raise MadcowError('A new bot has been created at %s, please modify config and rerun' % base)

    os.environ['MADCOW_BASE'] = base
    log = get_logger('madcow', stream=sys.stdout, unique=False)

    try:
        log.info('setting up http')
        http.setup(cookies=settings.HTTP_COOKIES, agent=settings.HTTP_AGENT, timeout=settings.HTTP_TIMEOUT)

        log.info('loading protocol handler')
        protocol = __import__('madcow.protocol', globals(), locals(), [settings.PROTOCOL])
        protocol = getattr(protocol, settings.PROTOCOL).ProtocolHandler

        if settings.DETACH and protocol.allow_detach:
            log.info('turning into a daemon')
            daemonize()

        if os.path.exists(settings.PIDFILE):
            log.warn('removing stale pidfile')
            os.remove(settings.PIDFILE)
        with open(settings.PIDFILE, 'wb') as fp:
            fp.write(str(os.getpid()))

        protocol(base).start()

    except:
        log.exception('A fatal error ocurred')
        raise

    finally:
        if os.path.exists(settings.PIDFILE):
            log.info('removing pidfile')
            os.remove(settings.PIDFILE)
