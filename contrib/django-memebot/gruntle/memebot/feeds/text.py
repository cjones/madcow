"""All links posted to #hugs, text-only SFW version"""

from memebot.feeds import hugs

class Feed(hugs.Feed):

    title = hugs.Feed.title + ' [text]'
    description = __doc__
    format = 'text'
