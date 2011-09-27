"""Provides embedded youtube video for youtube links"""

from django.conf import settings
from gruntle.memebot.scanner import Scanner, ScanResult, InvalidContent
from gruntle.memebot.utils.browser import render_node
from gruntle.memebot.utils import trapped

class YouTubeScanner(Scanner):

    rss_template = 'memebot/scanner/rss/youtube.html'

    url_match = {'netloc_regex': r'^(?:www\.)?youtube\.com$',
                 'netloc_ignorecase': True,
                 'path': '/watch',
                 'queries': (
                     {'key': 'v', 'val_regex': '^(.+)$'},
                     ),
                 }

    def __init__(self, *args, **kwargs):
        extra_attr = kwargs.pop('extra_attr', None)
        super(YouTubeScanner, self).__init__(*args, **kwargs)
        if extra_attr is None:
            extra_attr = settings.SCANNER_YOUTUBE_EXTRA_ATTR
        self.extra_attr = extra_attr

    def handle(self, response, log, video_id):
        attr = {'video_id': video_id}

        title = None
        if response.data_type == 'soup':
            soup = response.data
            with trapped:
                title = render_node(soup.head.title)
            if self.extra_attr:
                desc = soup.find('div', id='watch-description-clip')

                # this describes what we need to scrape.. youtube is awfully structured.
                # NOTE: this is stupidly slow.. disable if doing any volume.
                for row in (('uploader', desc, 'p',    'id',    'watch-uploader-info',           None),
                            ('summary',  desc, 'p',    'id',    'eow-description',               None),
                            ('category', desc, 'p',    'id',    'eow-category',                  None),
                            ('license',  desc, 'p',    'id',    'eow-reuse',                     None),
                            ('views',    soup, 'span', 'class', 'watch-view-count',              None),
                            ('extras',   soup, 'ul',   'id',    'watch-description-extra-info', 'li' ),
                            ('tags',     desc, 'ul',   'id',    'eow-tags',                      'a' )):
                    with trapped:

                        name, parent, tag, key, val, multi = row
                        node = parent.find(tag, **{key: val})
                        attr[name] = [render_node(s) for s in node(multi)] if multi else render_node(node)

        return ScanResult(response=response,
                          override_url=None,
                          title=title,
                          content_type=None,
                          content=None,
                          attr=attr)


scanner = YouTubeScanner()
