"""Protocol template"""

from madcow import Madcow, Request
import logging as log
import os

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
        while self.running:
            try:
                # in a real protocol, this should not block, otherwise
                # incoming messages do not get processed
                line = raw_input('>>> ')

                # send message to bot subsystem for processing
                self.process_message(line, os.environ['USER'])

                # check if we have any responses
                self.check_response_queue()

            except KeyboardInterrupt:
                self.running = False
            except EOFError:
                self.running = False
            except Exception, e:
                log.exception(e)

    def botName(self):
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
        self.checkAddressing(req)

        # pass to substem for final processing
        Madcow.process_message(self, req)

