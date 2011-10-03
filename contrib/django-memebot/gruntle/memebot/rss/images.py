"""All images posted to #hugs (resized and cached locally)"""

from gruntle.memebot.rss import Feed
from gruntle.memebot.rss.hugs import AllHugsLinksFeed

class HugsImageFeed(AllHugsLinksFeed):

    title = '#hugs images'
    description = __doc__

    def filter(self, published_links):
        """Filter published links to the ones we care about"""
        links = super(HugsImageFeed, self).filter(published_links)
        return links.filter(content_type__startswith='image/')


feed = HugsImageFeed()
