"""Embedded IPython hooks"""

from madcow import Madcow, Request
import os
import sys
from IPython.Shell import IPShellEmbed, kill_embedded
from IPython.ipmaker import make_IPython
from IPython import ipapi
from IPython import ultraTB
from IPython.iplib import InteractiveShell

COLOR_SCHEME = 'ansi'

class InteractiveShellMadcow(InteractiveShell):

    def handle_normal(self, line):
        if line.line.startswith('$'):
            self.callback.process_message(line.line[1:])
            self.callback.check_response_queue()
            return ''
        return InteractiveShell.handle_normal(self, line)


class IPShellMadcow(IPShellEmbed):

    def __init__(self,argv=None,banner='',exit_msg=None,rc_override=None,
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

    def __init__(self, base, scheme=None):
        """Protocol-specific initializations"""
        if scheme is None:
            scheme = COLOR_SCHEME
        super(IPythonHandler, self).__init__(base, scheme)

    def stop(self):
        """Protocol-specific shutdown procedure"""
        Madcow.stop(self)

    def run(self):
        """Protocol-specific loop"""
        print 'Prepend any messages you wish to pass to the both with a "$"'
        print 'self = %s' % self
        sys.argv = []
        shell = IPShellMadcow(callback=self)
        shell()

    def botname(self):
        """Should return bots real name for addressing purposes"""
        return 'madcow'

    def protocol_output(self, message, req=None):
        """Protocol-specific output method"""
        if req is not None and req.colorize is True:
            message = self.colorlib.rainbow(message)
        print message.encode(self.charset, 'replace')

    def process_message(self, message):
        """Create request object from recived message and process it"""
        req = Request(message=message)
        req.nick = os.environ['USER']
        req.channel = 'ipython'
        req.addressed = True
        self.check_addressing(req)
        Madcow.process_message(self, req)


class ProtocolHandler(IPythonHandler):

    allow_detach = False
