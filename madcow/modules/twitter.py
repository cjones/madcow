#!/usr/bin/env python
#
# Copyright (C) 2013 Mark Dobrowolski <markaci@gmail.com>, Remco Brink <remco@rc6.org>
#
# Usage:
#   twitter [user] - shows the last tweet by the specified user
#

"""Read from Twitter"""

import re
from madcow.util import Module
from madcow.conf import settings
from urlparse import urljoin
import oauth2 as oauth
try:
    import simplejson as json
except ImportError:
    import json
    
import logging as log

class TwitterAPI(object):
    API_URL = u"https://api.twitter.com/1.1/"
    USER_TIMELINE = u"statuses/user_timeline.json"
    
    def __init__(self, consumer_key, consumer_secret, token_key, token_secret, logger=None):
        self.token = oauth.Token(key=token_key, secret=token_secret)
        self.consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
        self.client = oauth.Client(self.consumer, self.token)
        self.log = logger

    def get_latest_tweet(self, username):
        resp, content = self.client.request(u"%s%s?screen_name=%s" % (self.API_URL, self.USER_TIMELINE, username))
        statuses = json.loads(content)
        try:
            return statuses[0].get(u'text', None)
        except Exception as e:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
            return None


class Main(Module):
    enabled = True
    pattern = re.compile(u'^\s*(?:twitter|tweet)(?:\s+(\S+))?')
    require_addressing = True
    help = u'tweet [user] - get latest tweet from user'

    def __init__(self, bot=None):
        super(Main, self).__init__(bot)
        self.twitter = TwitterAPI(settings.TWITTER_CONSUMER_KEY,
                                  settings.TWITTER_CONSUMER_SECRET,
                                  settings.TWITTER_TOKEN_KEY,
                                  settings.TWITTER_TOKEN_SECRET,
                                  log)

    def response(self, nick, args, kwargs):
        try:
            try:
                user = args[0]
            except:
                user = None
            if user in (None, u''):
                return u"%s: No username specified." % nick
	    else:
                tweet = self.twitter.get_latest_tweet(user)
                if tweet in (None, u''):
                    return u'%s: Unable to get latest tweet from user' % nick
                else:
                    return u'%s: %s' % (nick, tweet)
        except Exception as error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
