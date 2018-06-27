"""protocol support for slack websockets"""

import time
import sys
import os
import re

import slacksocket

from madcow.util.text import *

from madcow import Madcow
from madcow.util import Request
from madcow.conf import settings


class SlackProtocol(Madcow):

    def __init__(self, base):
        super(SlackProtocol, self).__init__(base)
        self.slack = slacksocket.SlackSocket(settings.SLACK_TOKEN, translate=True)
        self.channels = settings.SLACK_CHANNELS
        self.online = False

    def queue_checker(self):
        while self.running:
            self.check_response_queue()
            time.sleep(0.5)

    @staticmethod
    def fixlinks(t, s=re.compile(r'[<](https?://.*?)[>]').search, j=''.join):
        while True:
            m = s(t)
            if m is None:
                break
            x, y = t[:m.start()], t[m.end():]
            t = j([x, ' ' if x else '', m.group(1), ' ' if y else '', y])
        return t

    def run(self):
        while self.running:
            try:
                self.check_response_queue()
                try:
                    event = self.slack._eventq.get(False)
                except IndexError:
                    time.sleep(.2)
                else:
                    self.log.info(u'[SLACK] * %s', event.json)
                    event_type = event.event.get('type', 'unknown')
                    if event_type == 'hello':
                        self.online = True
                    elif self.online:
                        if event_type == 'message':
                            private = False  # TODO need to determine if this is in DM
                            req = Request(message=self.fixlinks(event.event['text']))
                            req.nick = event.event['user']
                            req.channel = event.event['channel']
                            req.private = private
                            if private:
                                req.sendto = req.nick
                                req.addressed = True
                            else:
                                req.sendto = req.channel
                                req.addressed = False
                            req.message = decode(req.message)
                            self.check_addressing(req)
                            req.colorize = False
                            self.process_message(req)
            except KeyboardInterrupt:
                self.running = False
            except:
                self.log.exception('Error in slack event loop')

    def protocol_output(self, message, req=None):
        if req.sendto is None:
            req.sendto = req.channel
        if req.blockquoted and u'```' not in message:
            message = u'```{}```'.format(message)
        else:
            if req.redquoted:
                fmt = u'`{}`'
                skip_re = re.compile(ur'`')
            elif req.quoted:
                fmt = u'> {}'
                skip_re = re.compile(ur'^>')
            else:
                fmt = None
                skip_re = None
            if fmt is not None:
                lines = []
                for line in message.splitlines():
                    line = line.strip()
                    if line:
                        if skip_re is None or skip_re.search(line) is None:
                            line = fmt.format(line)
                        lines.append(line)
                message = u'\n'.join(lines)

        if message:
            for channel in (self.channels if req.sendto == 'ALL' else [req.sendto]):
                self.slack.send_msg(message, channel_name=channel)
                self.logpublic(channel, '<%s> %s' % (self.botname(), encode(message)))


class ProtocolHandler(SlackProtocol):

    allow_detach = True
