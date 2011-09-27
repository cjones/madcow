"""MemeBot exceptions"""

class MemebotError(StandardError):

    """Base error class for memebot"""


class OldMeme(MemebotError):

    """Raised when a URL is reposted public"""

    def __init__(self, link):
        self.link = link

    def __str__(self):
        return 'Oldest meme EVAR! %r' % self.link
