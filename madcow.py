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

"""Madcow infobot"""

import sys

# verify python version is high enough
if sys.version_info[0] * 10 + sys.version_info[1] < 25:
    error = RuntimeError('madcow requires python 2.5 or higher')
    if __name__ == '__main__':
        print >> sys.stderr, error
        sys.exit(1)
    else:
        raise error

import os
from ConfigParser import ConfigParser
from optparse import OptionParser
import re
from time import sleep, strftime, time as unix_time
import logging as log
from select import select
from signal import signal, SIGHUP, SIGTERM
import shutil
from threading import Thread, RLock
from Queue import Queue, Empty
from hashlib import md5
import codecs
from include.authlib import AuthLib
from include.utils import Error, slurp, Request
from include import useragent as ua, gateway, chardet

__version__ = '1.4.2'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = ['Madcow']

MADCOW_URL = 'http://code.google.com/p/madcow/'
CHARSET = 'utf-8'
CONFIG = 'madcow.ini'
SAMPLE_HASH = 'fdb9fb43226e6990dd31b59dcd297ec7'
LOG = dict(level=log.WARN, stream=sys.stderr, datefmt='%x %X',
           format='[%(asctime)s] %(levelname)s: %(message)s')

class Madcow(object):

    """Core bot handler, subclassed by protocols"""

    _delim = re.compile(r'\s*[,;]\s*')
    _botname = 'madcow'
    re_cor1 = None
    re_addrend = None
    re_feedback = None
    re_cor2 = None
    re_addrpre = None

    ### INITIALIZATION FUNCTIONS ###

    def __init__(self, config, prefix):
        """Initialize bot"""
        self.config = config
        self.prefix = prefix
        self.cached_nick = None
        self.namespace = self.config.modules.dbnamespace
        self.running = False

        # parse ignore list
        if self.config.main.ignorelist is not None:
            self.ignore_list = self.config.main.ignorelist
            self.ignore_list = self._delim.split(self.ignore_list)
            self.ignore_list = [nick.lower() for nick in self.ignore_list]
            log.info('Ignoring nicks: %s' % ', '.join(self.ignore_list))
        else:
            self.ignore_list = []

        # create admin instance
        self.admin = Admin(self)

        # set encoding
        self.charset = CHARSET
        if self.config.main.charset:
            try:
                self.charset = codecs.lookup(self.config.main.charset).name
            except LookupError:
                log.warn('unknown charset %s, using default %s' % (
                    self.config.main.charset, self.charset))

        # load modules
        self.modules = Modules(self, 'modules', self.prefix)
        self.periodics = Modules(self, 'periodic', self.prefix)
        self.usage_lines = self.modules.help + self.periodics.help
        self.usage_lines.append('help - this screen')
        self.usage_lines.append('version - get bot version')

        # signal handlers
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
            log.info('starting service: %s' % service.__name__)
            thread = service(self)
            thread.setDaemon(True)
            thread.start()

        # start worker threads
        for i in range(0, self.config.main.workers):
            name = 'ModuleWorker' + str(i + 1)
            log.debug('Starting Thread: %s' % name)
            thread = Thread(target=self.request_handler, name=name)
            thread.setDaemon(True)
            thread.start()

        self.run()

    def run(self):
        """Runs madcow loop"""
        while self.running:
            # this is where you do actual stuff
            sleep(1)

    def signal_handler(self, sig, *args):
        """Handles signals"""
        if sig == SIGTERM:
            log.warn('got SIGTERM, signaling shutting down')
            self.running = False
        elif sig == SIGHUP:
            self.reload_modules()

    def reload_modules(self):
        """Reload all modules"""
        log.info('reloading modules')
        self.modules.load_modules()
        self.periodics.load_modules()

    ### OUTPUT FUNCTIONS

    def output(self, message, req=None):
        """Add response to output queue"""
        self.response_queue.put((message, req))

    def check_response_queue(self):
        """Check if there's any message in response queue and process"""
        try:
            response, req = self.response_queue.get_nowait()
        except Empty:
            return
        except Exception, exc:
            log.exception(exc)
            return
        self.handle_response(response, req)

    def handle_response(self, response, req=None):
        """encode output, lock threads, and call protocol_output"""
        response = self.encode(response)
        try:
            self.lock.acquire()
            try:
                self.protocol_output(response, req)
            except Exception, exc:
                log.error('error in output: %s' % repr(response))
                log.exception(exc)
        finally:
            self.lock.release()

    def encode(self, text):
        """Force output to the bots encoding if possible"""

        # see if we can figure out what this is string is encoded as
        try:
            detected = chardet.detect(text)['encoding']
        except Exception, error:
            log.warn('error detecting charset for: %s' % repr(text))
            log.exception(error)

        # try to convert to unicode, using utf8/windows/latin1 as failback
        for charset in detected, 'utf-8', 'cp1252', 'iso8859-1':
            if not charset:
                continue
            try:
                decoder = codecs.lookup(charset)
            except LookupError, error:
                log.warn("couldn't find codec for " + charset)
                log.exception(error)
                continue
            try:
                text = decoder.decode(text)[0]
                break
            except UnicodeError, error:
                log.warn('failed encoding to ' + charset)
                log.exception(error)

        # if all that failed, who knows. ascii with ?'s is better than nothing
        if isinstance(text, str):
            text = text.decode('ascii', 'replace')

        # return bytes encoded in the bot's character set
        return text.encode(self.charset, 'replace')

    def protocol_output(self, message, req=None):
        """Override with protocol-specific output method"""
        print message

    ### MODULE PROCESSING ###

    def request_handler(self):
        """Dispatcher for workers"""
        while self.running:
            request = self.request_queue.get()
            try:
                self.process_module_item(request)
            except Exception, e:
                log.exception(e)

    def process_module_item(self, request):
        """Run module response method and output any response"""
        obj, nick, args, kwargs = request
        try:
            response = obj.response(nick, args, kwargs)
        except Exception, exc:
            log.warn('Uncaught module exception')
            log.exception(exc)
            return

        if response is not None and len(response) > 0:
            self.output(response, kwargs['req'])

    ### INPUT FROM USER ###

    def check_addressing(self, req):
        """Is bot being addressed?"""
        nick = re.escape(self.botname())

        # recompile nick-based regex if it changes
        if nick != self.cached_nick:
            self.cached_nick = nick
            self.re_cor1 = re.compile(r'^\s*no[ ,]+%s[ ,:-]+\s*(.+)$' % nick,
                    re.I)
            self.re_cor2 = re.compile(r'^\s*no[ ,]+(.+)$', re.I)
            self.re_feedback = re.compile(r'^\s*%s[ !]*\?[ !]*$' % nick, re.I)
            self.re_addrend = re.compile(r'^(.+),\s+%s\W*$' % nick, re.I)
            self.re_addrpre = re.compile(r'^\s*%s[-,: ]+(.+)$' % nick, re.I)

        if self.re_feedback.search(req.message):
            req.feedback = req.addressed = True

        try:
            req.message = self.re_addrend.search(req.message).group(1)
            req.addressed = True
        except:
            pass

        try:
            req.message = self.re_addrpre.search(req.message).group(1)
            req.addressed = True
        except:
            pass

        try:
            req.message = self.re_cor1.search(req.message).group(1)
            req.correction = req.addressed = True
        except:
            pass

        if req.addressed:
            try:
                req.message = self.re_cor2.search(req.message).group(1)
                req.correction = True
            except:
                pass

    def process_message(self, req):
        """Process requests"""
        if 'NOBOT' in req.message:
            return
        if self.config.main.logpublic and not req.private:
            self.logpublic(req)
        if req.nick.lower() in self.ignore_list:
            log.info('Ignored "%s" from %s' % (req.message, req.nick))
            return
        if req.feedback:
            self.output('yes?', req)
            return
        if req.addressed and req.message.lower() == 'help':
            if self.config.main.module in ('irc', 'silcplugin'):
                req.sendto = req.nick
            self.output(self.usage(), req)
            return
        if req.addressed and req.message.lower() == 'version':
            res = 'madcow %s by %s: %s' % (__version__, __author__, MADCOW_URL)
            self.output(res, req)
            return
        if req.private:
            response = self.admin.parse(req)
            if response is not None and len(response):
                self.output(response, req)
                return
        if self.config.main.module == 'cli' and req.message == 'reload':
            self.reload_modules()
        for mod_name, obj in self.modules.by_priority():
            log.debug('trying: %s' % mod_name)

            if obj.require_addressing and not req.addressed:
                continue

            try:
                args = obj.pattern.search(req.message).groups()
            except:
                continue

            req.matched = True # module can set this to false to avoid term

            # see if we can filter some of this information..
            kwargs = {'req': req}
            kwargs.update(req.__dict__)
            request = (obj, req.nick, args, kwargs,)

            if self.config.main.module == 'cli' or not obj.allow_threading:
                log.debug('running non-threaded code for module %s' % mod_name)
                self.process_module_item(request)
            else:
                log.debug('launching thread for module: %s' % mod_name)
                self.request_queue.put(request)

            if obj.terminate and req.matched:
                log.debug('terminating because %s matched' % mod_name)
                break

    def logpublic(self, req):
        """Logs public chatter"""
        line = '%s <%s> %s\n' % (strftime('%T'), req.nick, req.message)
        path = os.path.join(
            self.prefix, 'logs',
            '%s-irc-%s-%s' % (self.namespace, req.channel, strftime('%F'))
        )

        logfile = open(path, 'a')
        try:
            logfile.write(line)
        finally:
            logfile.close()

    ### MISC FUNCTIONS ###

    def usage(self):
        """Returns help data as a string"""
        return '\n'.join(sorted(self.usage_lines))

    def stop(self):
        """Stop the bot"""
        self.running = False

    def botname(self):
        """Should return the real name of the bot"""
        return self._botname


class Service(Thread):

    """Service object"""

    def __init__(self, bot):
        self.bot = bot
        Thread.__init__(self, name=self.__class__.__name__)


class GatewayService(gateway.GatewayService, Service):

    """Gateway service spawns TCP socket and listens for requests"""


class PeriodicEvents(Service):

    """Class to manage modules which are periodically executed"""

    _re_delim = re.compile(r'\s*[,;]\s*')
    _ignore_modules = ['__init__', 'template']
    _process_frequency = 1
    last_run = {}

    def run(self):
        """While bot is alive, process periodic event queue"""
        delay = 5
        now = unix_time()
        for mod_name, obj in self.bot.periodics.dict().items():
            self.last_run[mod_name] = now - obj.frequency + delay

        while self.bot.running:
            self.process_queue()
            sleep(self._process_frequency)

    def process_queue(self):
        """Process queue"""
        now = unix_time()
        for mod_name, obj in self.bot.periodics.dict().items():
            if (now - self.last_run[mod_name]) < obj.frequency:
                continue
            self.last_run[mod_name] = now
            req = Request(None)
            req.sendto = obj.output
            request = (obj, None, None, {'req': req})
            self.bot.request_queue.put(request)


class FileNotFound(Error):

    """Raised when a file is not found"""


class ConfigError(Error):

    """Raised when a required config option is missing"""


class User(object):

    """This class represents a logged in user"""

    def __init__(self, user, flags):
        self.user = user
        self.flags = flags

    def is_asmin(self):
        """Boolean: user is an admin"""
        return 'a' in self.flags

    def is_registered(self):
        """Boolean: user is registerd"""
        if 'a' in self.flags or 'r' in self.flags:
            return True
        else:
            return False


class Admin(object):

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
        self.authlib = AuthLib('%s/data/db-%s-passwd' % (bot.prefix,
            bot.namespace))
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
            return self.register_user(nick, passwd)
        except:
            pass

        # log in
        try:
            passwd = self._reAuth.search(command).group(1)
            return self.authuser(nick, passwd)
        except:
            pass

        # help
        usage = []
        usage += self._basic_usage
        if nick in self.users:
            usage += self._loggedin_usage
            if self.users[nick].is_asmin():
                usage += self._admin_usage
        if self._reHelp.search(command):
            return '\n'.join(usage)

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
        if not user.is_asmin():
            return

        try:
            adduser, flags, password = self._reAddUser.search(command).groups()
            return self.adduser(adduser, flags, password)
        except:
            pass

        # be the puppetmaster
        try:
            channel, message = Admin._reFist.search(command).groups()
            req.sendto = channel
            return message
        except:
            pass

        # delete a user
        try:
            deluser = self._reDelUser.search(command).group(1)
            self.authlib.delete_user(deluser)
            if deluser in self.users:
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
                    if luser in self.users:
                        flags.append('loggedin')
                    flags = ' '.join(flags)
                    output.append('%s: %s' % (luser, flags))
                return '\n'.join(output)
        except:
            pass

        # update user flags
        try:
            chuser, newflags = self._reChFlag.search(command).groups()
            return self.change_flags(chuser, newflags)
        except:
            pass

    def change_flags(self, user, chflags):
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
        if user in self.users:
            self.users[user].flags = curflags
        return 'flags for %s changed to %s' % (user, curflags)

    def adduser(self, user, flags, password):
        """Add a new user"""
        if self.authlib.user_exists(user):
            return "User already registered."
        flags = ''.join(set(flags))
        self.authlib.add_user(user, password, flags)
        return 'user added: %s' % user

    def register_user(self, user, passwd):
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

    def authuser(self, user, passwd):
        """Attempt to log in"""
        if not self.authlib.user_exists(user):
            return "You are not registered: try register <password>."
        if not self.authlib.check_user(user, passwd):
            return 'Nice try.. notifying FBI'
        self.users[user] = User(user, self.authlib.get_flags(user))
        return 'You are now logged in. Message me "admin help" for help'


class Modules(object):

    """This class dynamically loads plugins and instantiates them"""

    _pyext = re.compile(r'\.py$')
    _ignore_mods = ('__init__', 'template')

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
        for mod_name, enabled in self.madcow.config.modules.settings.items():
            if not enabled:
                disabled.append(mod_name)
        log.info('reading modules from %s' % self.mod_dir)
        try:
            filenames = os.walk(self.mod_dir).next()[2]
        except Exception, exc:
            log.warn("Couldn't load modules from %s: %s" % (self.mod_dir, exc))
            return
        for filename in filenames:
            if not self._pyext.search(filename):
                continue
            mod_name = self._pyext.sub('', filename)
            if mod_name in disabled:
                log.debug('skipping %s: disabled' % mod_name)
                continue
            if mod_name in self.modules:
                mod = self.modules[mod_name]['mod']
                try:
                    reload(mod)
                    log.debug('reloaded module %s' % mod_name)
                except Exception, exc:
                    log.warn("couldn't reload %s: %s" % (mod_name, exc))
                    del self.modules[mod_name]
                    continue
            else:
                try:
                    mod = __import__(
                        '%s.%s' % (self.subdir, mod_name),
                        globals(),
                        locals(),
                        ['Main'],
                    )
                except Exception, exc:
                    log.warn("couldn't load module %s: %s" % (mod_name, exc))
                    continue
                self.modules[mod_name] = {'mod': mod}
            try:
                obj = getattr(mod, 'Main')(self.madcow)
            except Exception, exc:
                log.warn("failure loading %s: %s" % (mod_name, exc))
                del self.modules[mod_name]
                continue
            if not obj.enabled:
                log.debug("skipped loading %s: disabled" % mod_name)
                del self.modules[mod_name]
                continue
            try:
                if obj.help:
                    self.help.append(obj.help)
                else:
                    raise Exception
            except:
                log.debug('no help for module: %s' % mod_name)
            self.modules[mod_name]['obj'] = obj
            log.debug('loaded module: %s' % mod_name)

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


class Config(object):

    """Config class that allows dot-notation namespace addressing"""

    class ConfigSection:
        _isint = re.compile(r'^-?[0-9]+$')
        _isfloat = re.compile(r'^\s*-?(?:\d+\.\d*|\d*\.\d+)\s*$')
        _istrue = re.compile('^(?:true|yes|on|1)$', re.I)
        _isfalse = re.compile('^(?:false|no|off|0)$', re.I)

        def __init__(self, settings, name):
            self.name = name
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
            if attr in self.settings:
                return self.settings[attr]
            else:
                raise ConfigError, 'missing setting %s in section %s' % (
                        attr, self.name)


    def __init__(self, filename):
        if not os.path.exists(filename):
            raise FileNotFound, filename
        parser = ConfigParser()
        parser.read(filename)
        self.sections = {}
        for name in parser.sections():
            self.sections[name] = self.ConfigSection(parser.items(name), name)

    def __getattr__(self, attr):
        attr = attr.lower()
        if attr in self.sections:
            return self.sections[attr]
        else:
            raise ConfigError, "missing section: %s" % attr


def check_config(config, samplefile, prefix):
    """Sanity check config"""

    # this bloated, over-engineered routine exists because fucked up
    # config files are the #1 source of complaints about the bot being
    # "broken". maybe a more general solution can be done later. -CJ

    # verify we're using an unaltered sample file to verify against
    hash = md5()
    hash.update(slurp(samplefile))
    hash = hash.hexdigest()
    if hash != SAMPLE_HASH:
        print >> sys.stderr, 'WARNING: %s is out of date or has been altered!' \
            % os.path.basename(samplefile)

    # read sample file
    sample = ConfigParser()
    sample.read(samplefile)

    # problems stored here
    errors = []
    missing_sections = []
    missing_options = {}

    # look for valid protocols
    protocols = []
    for proto in os.walk(os.path.join(prefix, 'protocols')).next()[2]:
        try:
            name = re.search(r'^([^_]{2}\S+)\.py$', proto).group(1)
            if name == 'template':
                continue
            protocols.append(name)
        except AttributeError:
            continue

    # determine our protocol
    try:
        protocol = config.main.module
        if protocol not in protocols:
            errors.append('Invalid protocol %s, should be one of: %s' % (
                protocol, protocols))
    except ConfigError:
        errors.append('No protocol defined')
        protocol = None

    for section in sample.sections():
        # skip protocol sections that we aren't using
        if section in protocols and section != protocol:
            continue

        # see if the section even exists
        try:
            config_section = getattr(config, section)
        except ConfigError:
            missing_sections.append(section)
            continue

        # if section has an enabled flag and it's set to off,
        # then don't bother checking the other options
        if sample.has_option(section, 'enabled'):
            try:
                if not config_section.enabled:
                    continue
            except ConfigError:
                missing_options[section] = ['enabled']
                continue

        # verify options exist
        for option in sample.options(section):
            try:
                getattr(config_section, option)
            except ConfigError:
                missing_options.setdefault(section, [])
                missing_options[section].append(option)

    # construct list of errors
    if missing_sections:
        missing_sections = ['[%s]' % i for i in missing_sections]
        errors.append('Missing sections: ' + ','.join(missing_sections))
    for section, options in missing_options.items():
        errors.append('Section [%s] missing options: %s' % (section,
            ', '.join(options)))

    # raise exception if any errors are found
    if errors:
        raise ConfigError, '\n'.join(errors)


def main():
    """Entry point to set up bot and run it"""

    log.basicConfig(**LOG)

    # where we are being run from
    if __file__.startswith(sys.argv[0]):
        prefix = sys.argv[0]
    else:
        prefix = __file__
    prefix = os.path.abspath(os.path.dirname(prefix))
    sys.path.insert(0, prefix)
    default_config = os.path.join(prefix, CONFIG)

    # make sure proper subdirs exist
    for subdir in 'data', 'logs':
        path = os.path.join(prefix, subdir)
        if not os.path.exists(path):
            os.mkdir(path)

    # find available protocols
    protos = [proto.replace('.py', '')
              for proto in os.listdir(os.path.join(prefix, 'protocols'))
              if proto.endswith('.py')]

    # parse commandline options
    parser = OptionParser(version=__version__)
    parser.add_option(
            '-c', '--config', metavar='<file>', default=default_config,
            help='use config file (default: %default)')
    parser.add_option(
            '-d', '--detach', default=False, action='store_true',
            help='run process in the background')
    parser.add_option(
            '-p', '--protocol', metavar='<%s>' % '|'.join(protos),
            type='choice', choices=protos,
            help='force the use of this output protocol')
    parser.add_option(
            '-D', '--debug', dest='loglevel', action='store_const',
            const=log.DEBUG, help='show debug messages')
    parser.add_option(
            '-v', '--verbose', dest='loglevel', action='store_const',
            const=log.INFO, help='show info messages')
    parser.add_option(
            '-q', '--quiet', dest='loglevel', action='store_const',
            const=log.WARN, help='show only error messages')
    parser.add_option(
            '-P', '--pidfile', metavar='<file>',
            help='override pidfile (default: %default)')
    opts, args = parser.parse_args()

    if args:
        parser.error('invalid arguments')

    # read config file
    sample_config = default_config + '-sample'
    if not os.path.exists(opts.config):
        if opts.config == default_config:
            shutil.copyfile(sample_config, opts.config)
            log.error('created config %s - edit and rerun' % CONFIG)
        else:
            log.error('config not found: %s' % opts.config)
        return 1

    try:
        config = Config(opts.config)
    except FileNotFound:
        log.error('config file not found, see README')
        return 1
    except Exception, error:
        log.error('error parsing config: %s' % error)
        return 1

    try:
        check_config(config, sample_config, prefix)
    except ConfigError, error:
        log.error('%s is missing required settings, check %s' % (
                os.path.basename(opts.config),
                os.path.basename(sample_config)))
        return 1

    # init log facility
    try:
        loglevel = getattr(log, config.main.loglevel)
    except:
        loglevel = LOGLEVEL
    if opts.loglevel is not None:
        loglevel = opts.loglevel
    log.root.setLevel(loglevel)

    # if specified, log to file as well
    if config.main.logfile:
        handler = log.FileHandler(config.main.logfile)
        handler.setFormatter(log.Formatter(LOG['format'], LOG['datefmt']))
        log.root.addHandler(handler)

    # load specified protocol
    if opts.protocol:
        protocol = config.main.module = opts.protocol
    else:
        protocol = config.main.module

    # setup global UserAgent
    ua.setup(config.http.agent, config.http.cookies, [], config.http.timeout)

    # determine pidfile to use (commandline overrides config)
    if opts.pidfile:
        pidfile = opts.pidfile
    else:
        pidfile = config.main.pidfile

    # write pidfile. from this point on, capture ALL exceptions
    # so that the pidfile can be removed when we're done
    if pidfile:
        if os.path.exists(pidfile):
            log.warn('removing stale pidfile: %s' % pidfile)
            os.remove(pidfile)
        try:
            file = open(pidfile, 'wb')
            try:
                file.write(str(os.getpid()))
            finally:
                file.close()
        except Exception, error:
            log.warn('failed to write %s: %s' % (pidfile, error))
            log.exception(error)

    # import protocol handler
    handler = None
    try:
        module = __import__('protocols', globals(), locals(), [protocol])
        module = getattr(module, protocol)
        handler = getattr(module, 'ProtocolHandler')
    except ImportError:
        log.error('unknown protocol: ' + protocol)
    except AttributeError:
        log.error('no handler found for protocol: ' + protocol)
    except Exception, error:
        log.exception(error)

    if handler:
        # daemonize if requested, but not when interactive!
        if config.main.detach or opts.detach:
            if __name__ == '__main__':
                log.warn('not detaching in interactive shell')
            elif protocol == 'cli':
                log.warn('not detaching for commandline client')
            else:
                if os.fork():
                    sys.exit(0)
                os.setsid()
                if os.fork():
                    sys.exit(0)
                for stream in sys.stdout, sys.stderr:
                    stream.flush()
                devnull = file('/dev/null', 'a+', 0)
                for fd in range(3):
                    os.dup2(fd, devnull.fileno())
                log.info('madcow is launched as a daemon')

        # actually run bot
        try:
            bot = handler(config, prefix)
            bot.start()
        except Exception, error:
            log.error('fatal error in bot, shutting down')
            log.exception(error)

        # this would be in a finally block, but 2.4 compatibility :/
        try:
            bot.stop()
        except Exception, error:
            log.exception(error)

    if pidfile and os.path.exists(pidfile):
        log.info('removing pidfile')
        try:
            os.remove(pidfile)
        except Exception, error:
            log.warn('failed to remove pidfile %s' % pidfile)
            log.exception(error)

    log.info('madcow is shutting down')
    return 0

if __name__ == '__main__':
    sys.exit(main())
