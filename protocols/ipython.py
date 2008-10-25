"""Protocol template"""

from madcow import Madcow, Request
import logging as log
import os

import sys
from IPython.Shell import IPShellEmbed, kill_embedded
from IPython.ipmaker import make_IPython
from IPython import ipapi
from IPython import ultraTB
from IPython.iplib import InteractiveShell

bot = None

class InteractiveShellMadcow(InteractiveShell):

    def handle_normal(self, line):
        if line.line.startswith('madcow'):
            self.callback.process_message(line.line.encode('utf-8', 'replace'), 'cjones')
            self.callback.check_response_queue()
            return ''
        return line.line


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
        self.IP.callback = bot
        ip = ipapi.IPApi(self.IP)
        ip.expose_magic("kill_embedded",kill_embedded)
        self.sys_displayhook_embed = sys.displayhook
        sys.displayhook = self.sys_displayhook_ori
        sys.excepthook = ultraTB.FormattedTB(color_scheme = self.IP.rc.colors,
                                             mode = self.IP.rc.xmode,
                                             call_pdb = self.IP.rc.pdb)
        self.restore_system_completer()


class ProtocolHandler(Madcow):
    """This object is autoloaded by the bot"""

    def __init__(self, config, dir):
        """Protocol-specific initializations"""
        Madcow.__init__(self, config, dir)

    def stop(self):
        """Protocol-specific shutdown procedure"""
        Madcow.stop(self)

    def run(self):
        """Protocol-specific loop"""
        global bot
        bot = self
        shell = IPShellMadcow(callback=self)
        shell()

    def botname(self):
        """Should return bots real name for addressing purposes"""
        return 'madcow'

    def protocol_output(self, message, req=None):
        """Protocol-specific output method"""
        print message

    def process_message(self, message, nick):
        """Create request object from recived message and process it"""

        # this object persists as it's processed by the bot subsystem.
        # if this requests generates a response, you will receive it along
        # with the response message in protocol_output(), which means you
        # can set arbitrary attributes and access them later, for example
        # a channel to send to for multi-channel protocols, etc.
        req = Request(message)

        # required for most modules
        req.nick = nick

        # some modules expect this to be set as well as logging facility
        req.channel = 'console'

        # force bot into addressed mode
        # many modules require the bot is addressed before triggering.
        req.addressed = True

        # this sets the above flag to true if the user addresses the bot,
        # as well as strips off the bots nick.
        self.check_addressing(req)

        # pass to substem for final processing
        Madcow.process_message(self, req)

