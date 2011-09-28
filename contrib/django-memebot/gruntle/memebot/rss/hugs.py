"""#hugs MemeBot RSS Feed: All verifiable links, full rendering"""

from gruntle.memebot.rss import Feed

class AllHugsLinksFeed(Feed):

    title = 'All #hugs Links RSS Feed'
    description = __doc__
    max_links = 100

    def filter(self, published_links):
        """Filter published links to the ones we care about"""
        return published_links.filter(source__type='irc', source__name='#hugs')


feed = AllHugsLinksFeed()
