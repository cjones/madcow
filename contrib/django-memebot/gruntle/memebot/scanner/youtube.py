"""Provides embedded youtube video for youtube links"""

from gruntle.memebot.scanner import Scanner, ScanResult, InvalidContent

class YouTubeScanner(Scanner):

    rss_template = 'memebot/scanner/rss/youtube.html'

    url_match = {'netloc_regex': r'^(?:www\.)?youtube\.com$',
                 'netloc_ignorecase': True,
                 'path': '/watch',
                 'queries': (
                     {'key': 'v', 'val_regex': '^(.+)$'},
                     ),
                 }

    def handle(self, response, log, video_id):
        return ScanResult(response=response,
                          override_url=None,
                          title='Fake Title',
                          content_type=None,
                          content=None,
                          attr={'video_id': video_id})


scanner = YouTubeScanner()
