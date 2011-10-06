"""All images posted to #hugs (resized and cached locally)"""

from gruntle.memebot.feeds import hugs

class Feed(hugs.Feed):

    title = 'All #hugs Image URLs'
    description = __doc__

    def filter(self, published_links):
        """Filter published links to the ones we care about"""
        links = super(Feed, self).filter(published_links)
        return links.filter(content_type__startswith='image/')
