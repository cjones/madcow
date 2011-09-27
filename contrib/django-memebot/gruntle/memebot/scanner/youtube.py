"""Provides embedded youtube video for youtube links"""

from gruntle.memebot.scanner import Scanner, ScanResult

class YouTubeScanner(Scanner):

    url_match = {'netloc_regex': r'^(?:www\.)?youtube\.com$',
                 'netloc_ignorecase': True,
                 'path': '/watch',
                 'queries': (
                     {'key': 'w', 'val_regex': '^(.+)$'},
                     ),
                 }

    def handle(self, response, log, video_id):
        return ScanResult(response, None, 'A Youtube Video!', 'text/html', '<h3>YOUTUBE LOL!</h3>')


scanner = YouTubeScanner()
