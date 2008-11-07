"""Embedded IPython hooks"""

from madcow import Madcow, Request
import logging as log
import os
from include.colorlib import ColorLib
import sys
from IPython.Shell import IPShellEmbed, kill_embedded
from IPython.ipmaker import make_IPython
from IPython import ipapi
from IPython import ultraTB
from IPython.iplib import InteractiveShell

class InteractiveShellMadcow(InteractiveShell):

    def handle_normal(self, line):
        if line.line.startswith(u'$'):
            data = line.line[1:].encode(u'utf-8', u'replace')
            self.callback.process_message(data)
            self.callback.check_response_queue()
            return u''
        return InteractiveShell.handle_normal(self, line)


class IPShellMadcow(IPShellEmbed):

    def __init__(self,argv=None,banner=u'',exit_msg=None,rc_override=None,
                 user_ns=None, callback=None):
        self.set_banner(banner)
        self.set_exit_msg(exit_msg)
        self.set_dummy_mode(0)
        self.sys_displayhook_ori = sys.displayhook
        try:
            self.sys_ipcompleter_ori = sys.ipcompleter
        except:
            pass
        self.IP = make_IPython(argv,rc_override=rc_override,
                               embedded=True,
                               user_ns=user_ns,
                               shell_class=InteractiveShellMadcow)
        self.IP.callback = callback
        ip = ipapi.IPApi(self.IP)
        ip.expose_magic(u"kill_embedded",kill_embedded)
        self.sys_displayhook_embed = sys.displayhook
        sys.displayhook = self.sys_displayhook_ori
        sys.excepthook = ultraTB.FormattedTB(color_scheme = self.IP.rc.colors,
                                             mode = self.IP.rc.xmode,
                                             call_pdb = self.IP.rc.pdb)
        self.restore_system_completer()


class IPythonHandler(Madcow):

    """This object is autoloaded by the bot"""

    def __init__(self, config, dir):
        """Protocol-specific initializations"""
        self.colorlib = ColorLib(u'ansi')
        Madcow.__init__(self, config, dir)

    def stop(self):
        """Protocol-specific shutdown procedure"""
        Madcow.stop(self)

    def run(self):
        """Protocol-specific loop"""
        print u'Prepend any messages you wish to pass to the both with a "$"'
        print u'self = %s' % self
        sys.argv = []
        shell = IPShellMadcow(callback=self)
        shell()

    def botname(self):
        """Should return bots real name for addressing purposes"""
        return u'madcow'

    def protocol_output(self, message, req=None):
        """Protocol-specific output method"""
        print message

    def process_message(self, message):
        """Create request object from recived message and process it"""
        req = Request(message)
        req.nick = os.environ[u'USER']
        req.channel = u'ipython'
        req.addressed = True
        self.check_addressing(req)
        Madcow.process_message(self, req)


ProtocolHandler = IPythonHandler
