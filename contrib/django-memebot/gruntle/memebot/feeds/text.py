"""All links posted to #hugs (text only)"""

from gruntle.memebot.feeds import hugs

class Feed(hugs.Feed):

    title = hugs.Feed.title + ' (text only)'
    description = hugs.Feed.description + ' (text only)'
    format = 'text'
