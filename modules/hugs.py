#!/usr/bin/env python

# Get a random confession from grouphug.us

import sys
import re
import urllib
from include import utils

# class for this module
class MatchObject(object):
    def __init__(self, config=None, ns='default', dir=None):
        self.enabled = True                # True/False - enabled?
        self.pattern = re.compile('^\s*hugs(?:\s+(\d+))?')    # regular expression that needs to be matched
        self.requireAddressing = True            # True/False - require addressing?
        self.thread = True                # True/False - should bot spawn thread?
        self.wrap = True                # True/False - wrap output?
        self.help = 'hugs - random confession'

        self.confs = re.compile('<p>(.*?)</p>', re.I + re.DOTALL)

    # function to generate a response
    def response(self, *args, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        try:
            if args[0] is not None:
                url = 'http://grouphug.us/confessions/' + args[0]
            else:
                url = 'http://grouphug.us/random'

            doc = urllib.urlopen(url).read()

            conf = self.confs.findall(doc)[0]
            conf = utils.stripHTML(conf)
            conf = conf.strip()

            return conf
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: I had some issues with that..' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
    if argv is None: argv = sys.argv[1:]
    obj = MatchObject()
    print obj.response(nick='testUser', args=argv)

    return 0

if __name__ == '__main__': sys.exit(main())
