"""Prints tweets to the channel."""

from itertools import product, izip, imap, tee
from operator import attrgetter
from madcow.conf import settings
from madcow.util import strip_html, Task
from pprint import pformat
from twitter.error import TwitterError
from twitter import Api
from datetime import timedelta
import time
import sys

_getid = attrgetter('id')

class APIError(Exception):

    @classmethod
    def from_twitter_error(cls, exc_value):
        msgs = []
        for errors in exc_value.args:
            for error in errors:
                opts = dict(error)
                msg = opts.pop('message', None)
                if not msg:
                    msg = u'Unknown Error'
                num = opts.pop('code', None)
                if num is not None:
                    msg += u' (Err#{})'.format(num)
                msgs.append(msg)
        message = u'\n'.join(msgs)
        if not message.strip():
            message = u'No Error Message'
        return cls(message, orig_exc=exc_value)

    def __init__(self, message=None, orig_exc=None):
        self.orig_exc = orig_exc
        super(APIError, self).__init__(message)


class Main(Task):

    defaults = {
            'consumer_key': None,
            'consumer_secret': None,
            'access_token_key': None,
            'access_token_secret': None,
            'disable_cache': True,
            'output': 'ALL',
            'update_freq': 45,
            'tweet_format': u'>> tweet from {tweet.user.screen_name}: {tweet.text_clean} <<',
            'err_announce': True,
            'err_announce_freq': timedelta(hours=8).total_seconds(),
            'soft_limit': 10,
            }

    _setting_prefix = 'TWITTER_'

    log = property(lambda s: s.madcow.log)

    def __new__(cls, *args, **opts):
        obj = super(Main, cls).__new__(cls, *args, **opts)
        obj.ready = False
        return obj

    def init(self):
        opts = {}
        for key, default in self.defaults.iteritems():
            setting = self._setting_prefix + key.upper()
            val = getattr(settings, setting, None)
            if val is None:
                val = default
            opts[key] = val
        x, y = tee(imap('{}_{}'.format, *izip(*product(['consumer', 'access_token'], ['key', 'secret']))))
        self.api = Api(**dict(izip(x, imap(opts.pop, y))))
        if opts.pop('disable_cache'):
            self.api.SetCache(None)
        self.last_error_announce = 0
        self.last_id = None
        vars(self).update(opts)

        try:
            status = self.api.VerifyCredentials()
        except TwitterError, exc:
            exc_info = sys.exc_info()
            error = APIError.from_twitter_error(exc)
            self.log.error('twitter oAuth2 failure, disabling task: {}'.format(error.message))
            self.unload()
            reraise(*exc_info)
        else:
            self.log.info('twitter oAuth2 verified, response:\n' + pformat(status))

        self.ready = True

    def unload(self):
        """unloads module/task from the bot."""
        for ctx, desc in [(self.madcow.modules, 'plugin'), (self.madcow.tasks, 'periodic task')]:
            disabled = [name for name, info in ctx.modules.iteritems()
                        if self is info['obj'] and cls is info['mod'].Main]
            for name in disabled:
                info = ctx.modules.pop(name)
                info['mod'].Main.enabled = False
                vars(info['obj']).clear()
                self.log('disabled and unloaded {}: {}'.format(desc, name))

    def response(self, *args, **opts):
        """called periodically according to update_freq"""
        if self.ready:
            try:
                return self._response(*args, **opts)
            except APIError, exc:
                self.log.exception()
                if self.err_announce:
                    now = time.time()
                    elapsed = now - self.last_error_announce
                    if elapsed >= self.err_announce_freq:
                        self.last_error_announce = now
                        return exc.message

    def _response(self, *args):
        try:
            status = self.api.GetRateLimitStatus()
            if status['resources']['statuses']['/statuses/home_timeline']['remaining'] < self.soft_limit:
                self.log.warn('twittter rate limit soft threshold exceeded:\n' + pformat(status))
                raise APIError('Hit the Twitter ratelimit, backing off. Reduce the update frequency.')

            tweets = self.api.GetHomeTimeline(since_id=self.last_id)
            if tweets:
                lines = []
                new_last_id = _getid(max(tweets, key=_getid))
                try:
                    if self.last_id is not None:
                        for tweet in sorted(tweets, key=_getid):
                            if tweet.id > self.last_id:
                                tweet.text_clean = strip_html(tweet.text)
                                lines.append(self.tweet_format.format(tweet=tweet))

                finally:
                    self.last_id = new_last_id
                if lines:
                    return u'\n'.join(lines)
        except TwitterError, exc:
            raise APIError.from_twitter_error(exc)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            raise APIError('unhandled exception: {}'.format(sys.exc_value), orig_exc=sys.exc_value)


def reraise(exc_type, exc_value, exc_traceback):
    raise exc_type, exc_value, exc_traceback
