"""Default MemeBot RSS Feed: All verifiable links, fully rendered"""

from gruntle.memebot.rss import Feed

class DefaultFeed(Feed):

    description = __doc__

    def filter(self, published_links):
        """Filter published links to the ones we care about"""
        return published_links


feed = DefaultFeed()
