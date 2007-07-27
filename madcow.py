#!/usr/bin/env python

__version__ = '1.1.0'
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
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL


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


class Madcow(object):
    """
    Core bot handler
    """

    def __init__(self, config=None, dir=None):
        self.config = config
        self.dir = dir

        self.ns = self.config.modules.dbnamespace
        self.ignoreModules = [ '__init__', 'template' ]
        self.ignoreModules.append('tac')       # moved to grufti framework in 1.0.7
        self.ignoreModules.append('bullshitr') # moved to grufti framework in 1.0.7
        self.moduleDir = self.dir + '/modules'
        self.outputLock = threading.RLock()

        # dynamically generated content
        self.usageLines = []
        self.modules = {}
        self.loadModules()

    def status(self, msg=None, level=INFO):
        logging.log(msg=msg, level=level)

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
        self.status('[MOD] * Reading modules from %s' % self.moduleDir, INFO)

        for file in files:
            if file.endswith('.py') is False:
                continue

            modName = file[:-3]
            if modName in self.ignoreModules:
                continue

            if modName in disabled:
                self.status('[MOD] Skipping %s because it is disabled in config' % modName, WARN)
                continue

            try:
                module = __import__('modules.' + modName, globals(), locals(), ['MatchObject'])
                MatchObject = getattr(module, 'MatchObject')
                obj = MatchObject(config=self.config, ns=self.ns, dir=self.dir)

                if obj.enabled is False:
                    raise Exception, 'disabled'

                if hasattr(obj, 'help') and obj.help is not None:
                    self.usageLines += obj.help.splitlines()

                self.status('[MOD] Loaded module %s' % modName, INFO)
                self.modules[modName] = obj

            except Exception, e:
                self.status("[MOD] WARN: Couldn't load module %s: %s" % (modName, e), WARN)

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

    def usage(self):
        """
        Returns help data as a string
        """
        return '\n'.join(self.usageLines)

    def processMessage(self, req):
        """
        Process requests
        """
        if req.feedback is True:
            self.output('yes?', req)
            return

        if req.addressed is True and req.message.lower() == 'help':
            self.output(self.usage(), req)
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
                response = module.response(**kwargs)
                if response is not None and len(response) > 0:
                    self.output(response, req)

    def processThread(self, **kwargs):
        response = kwargs['module'].response(**kwargs)
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
    logging.basicConfig(level=WARN, format='[%(asctime)s] %(levelname)s: %(message)s')
    if opts.debug:
        logging.root.setLevel(DEBUG)
    elif opts.verbose:
        logging.root.setLevel(INFO)

    # read config file
    config = Config(file=opts.config)

    # load specified protocol
    if opts.protocol:
        protocol = opts.protocol
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
