#!/usr/bin/env python

"""
This is the template for creating your own user modules.  Copy this file
to something unique (it must end with .py!).  Edit the __init__ function.  This is
where you set what regular expression will trigger the process() call when run
within the bot, whether it should spawn a new thread when running response(), and whether
addressing is required for the bot to trigger this addon.

The response() function is where your script goes, it should return a response or None.

kwargs is a dict passed from the bot. this allows you to develop
more advanced modules that require introspection. the following
key/value pairs are made available:

<string>  nick       - nickname of the user invoking the module
<string>  channel    - channel that module was triggered from
<boolean> addressed  - True/False, whether bot was addressed by name
<boolean> correction - True/False, whether user was correcting the bot
<list>    args       - list of args trapped from the regex above.
"""

import sys
import re
import os


class MatchObject(object):
    """
    This object is autoloaded by the bot
    """

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.ns = ns
        self.dir = dir
        self.config = config

        self.enabled = True
        self.pattern = re.compile('^\s*keyword\s+(\S+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = None

    def response(self, **kwargs):
        """
        This function should return a response to the query or None.
        """

        nick = kwargs['nick']
        args = kwargs['args']

        try:
            pass
        except Exception, e:
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
