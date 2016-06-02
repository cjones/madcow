"""protocol support for slack websockets"""

import threading
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


    def run(self):
        queue_thread = threading.Thread(target=self.queue_checker)
        queue_thread.start()
        while self.running:
            event = self.slack.get_event()
            self.log.info(u'[SLACK] * %s', event.json)
            event_type = event.event.get('type', 'unknown')
            if event_type == 'hello':
                self.online = True
            elif self.online:
                if event_type == 'message':
                    req = Request(message=event.event['text'])
                    req.nick = event.event['user']
                    req.channel = event.event['channel']
                    req.private = False
                    self.check_addressing(req)
                    self.process_message(req)

    def protocol_output(self, message, req=None):
        if req.sendto is None:
            req.sendto = req.channel
        for channel in (self.channels if req.sendto == 'ALL' else [req.sendto]):
            self.slack.send_msg(message, channel_name=channel)
            self.logpublic(channel, '<%s> %s' % (self.botname(), encode(message)))


class ProtocolHandler(SlackProtocol):

    allow_detach = True
