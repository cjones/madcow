
class URLBotError(StandardError):

    pass


class OldMeme(URLBotError):

    def __init__(self, link):
        self.link = link

    def __str__(self):
        return 'Oldest meme EVAR! %r' % self.link
