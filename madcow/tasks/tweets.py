"""Prints tweets to the channel."""

import time
import twitter
from madcow.conf import settings
from madcow.util import strip_html, Task

class Main(Task):

    def init(self):
        self.frequency = settings.TWITTER_UPDATE_FREQ
        self.output = settings.TWITTER_CHANNELS
        self.api = twitter.Api(username=settings.TWITTER_CONSUMER_KEY,
                               password=settings.TWITTER_CONSUMER_SECRET,
                               access_token_key=settings.TWITTER_TOKEN_KEY,
                               access_token_secret=settings.TWITTER_TOKEN_SECRET)
        self.api.SetCache(None)  # this fills up /tmp :(
        self.last = time.time()

    def response(self, *args):
        return 'this is a response'
        status = self.api.GetRateLimitStatus()
        self.log.debug('rate limit status: %r' % status)
        if status['remaining_hits'] < 10:
            raise ValueError('Hitting the Twitter limit, backing off!')

        self.log.debug(u'getting tweets...')
        tweets = self.api.GetFriendsTimeline()

        log.debug(u'found %d tweets, parsing' % len(tweets))
        lines = []
        for tweet in reversed(tweets):
            time_of_tweet = tweet.GetCreatedAtInSeconds()
            if time_of_tweet >= self.last:
                lines.append(u">> tweet from %s: %s <<" % (tweet.user.screen_name, strip_html(tweet.text)))

        if lines:
            self.last = time.time()
            return u"\n".join(lines)
