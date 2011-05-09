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
        self.last_id = None

    @staticmethod
    def get_max_id(tweets):
        return max(tweets, key=lambda tweet: tweet.id).id

    def response(self, *args):
        self.log.debug('checking twitter for new tweets')
        status = self.api.GetRateLimitStatus()
        self.log.debug('rate limit status: %r', status)
        if status['remaining_hits'] < 10:
            raise ValueError('Hitting the Twitter limit, backing off!')

        # first run, just throw away all
        if self.last_id is None:
            self.last_id = self.get_max_id(self.api.GetFriendsTimeline())
            self.log.info('set last twitter id to %d', self.last_id)
        else:
            tweets = self.api.GetFriendsTimeline(since_id=self.last_id)
            if tweets:
                lines = []
                for tweet in reversed(tweets):
                    if tweet.id > self.last_id:
                        lines.append(u">> tweet from %s: %s <<" % (tweet.user.screen_name, strip_html(tweet.text)))
                self.last_id = self.get_max_id(tweets)
                if lines:
                    return u'\n'.join(lines)
