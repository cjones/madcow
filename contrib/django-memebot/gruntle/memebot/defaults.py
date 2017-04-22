from __future__ import unicode_literals

import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from mezzanine.conf import register_setting


register_setting(
    name="FEED_DIR",
    editable=False,
    default=os.path.join(settings.MEDIA_ROOT, "feeds"),
)

register_setting(
    name="FEED_WEBMASTER",
    editable=False,
    default='{} ({})'.format(settings.ADMINS[0][1], settings.ADMINS[0][0]),
)

register_setting(
    name="ANONYMOUS_USER_EMAIL",
    editable=False,
    default='nobody@localhost',
)

register_setting(
    name="AUTO_USER_ADD",
    editable=False,
    default=True,
)

register_setting(
    name="BROWSE_LINKS_PER_PAGE",
    editable=False,
    default=100,
)

register_setting(
    name="FEEDS",
    editable=False,
    default=('memebot.feeds.hugs', 'memebot.feeds.images', 'memebot.feeds.text'),
)

register_setting(
    name="FEED_BASE_URL",
    editable=False,
    default='http://gruntle.org/',
)

register_setting(
    name="FEED_COPYRIGHT",
    editable=False,
    default='Copyright © 2011 Madcow Industries',
)

register_setting(
    name="FEED_ENCODING",
    editable=False,
    default='UTF-8',
)

register_setting(
    name="FEED_EXTRA_NAMESPACES",
    editable=False,
    default=None,
)

register_setting(
    name="FEED_IMAGE_HEIGHT",
    editable=False,
    default=108,
)

register_setting(
    name="FEED_IMAGE_LINK",
    editable=False,
    default=None,
)

register_setting(
    name="FEED_IMAGE_TITLE",
    editable=False,
    default=None,
)

register_setting(
    name="FEED_IMAGE_URL",
    editable=False,
    default='http://gruntle.org/media/img/cow_icon_01.png',
)

register_setting(
    name="FEED_IMAGE_WIDTH",
    editable=False,
    default=144,
)

register_setting(
    name="FEED_KEEP_XML_BACKUP",
    editable=False,
    default=True,
)

register_setting(
    name="FEED_MAX_LINKS",
    editable=False,
    default=25,
)

register_setting(
    name="FEED_STYLESHEETS",
    editable=False,
    default=None,
)

register_setting(
    name="FEED_SUMMARY_CONT",
    editable=False,
    default='...',
)

register_setting(
    name="FEED_SUMMARY_SIZE",
    editable=False,
    default=512,
)

register_setting(
    name="FEED_TTL",
    editable=False,
    default=60,
)

register_setting(
    name="LOGIN_REDIRECT_URL",
    editable=False,
    default='/memebot/',
)

register_setting(
    name="LOG_DATE_FORMAT",
    editable=False,
    default='%Y-%m-%d %H:%M:%S',
)

register_setting(
    name="LOG_LEVEL",
    editable=False,
    default='INFO',
)

register_setting(
    name="LOG_MAX_FILES",
    editable=False,
    default=1000,
)

register_setting(
    name="LOG_DIR",
    editable=False,
    default=os.path.join(settings.MEDIA_ROOT, "logs"),
)

register_setting(
    name="LOG_PERMS",
    editable=False,
    default=420,
)

register_setting(
    name="LOG_RECORD_FORMAT",
    editable=False,
    default='%(asctime)s [%(levelname)s] %(message)s',
)

register_setting(
    name="MEMEBOT_BLACKLIST",
    editable=False,
    default=('localhost', '127.0.0.1', 'gruntle.org', '*.gruntle.org', 'ef.net', '*.ef.net'),
)

register_setting(
    name="MEMEBOT_POINTS_NEW",
    editable=False,
    default=1,
)

register_setting(
    name="MEMEBOT_POINTS_OLD",
    editable=False,
    default=-2,
)

register_setting(
    name="MEMEBOT_POINTS_REPOSTS",
    editable=False,
    default=2,
)

register_setting(
    name="SCANNERS",
    editable=False,
    default=('memebot.scanner.youtube', 'memebot.scanner.image', 'memebot.scanner.imgur', 'memebot.scanner.bolt', 'memebot.scanner.html', 'memebot.scanner.default'),
)

register_setting(
    name="SCANNER_IMAGE_MAX_SIZE",
    editable=False,
    default=(640, 480),
)

register_setting(
    name="SCANNER_IMAGE_RESIZE_ALG",
    editable=False,
    default='ANTIALIAS',
)

register_setting(
    name="SCANNER_IMAGE_TYPE",
    editable=False,
    default='png',
)

register_setting(
    name="SCANNER_MAX_ERRORS",
    editable=False,
    default=5,
)

register_setting(
    name="SCANNER_MAX_LINKS",
    editable=False,
    default=9999,
)

register_setting(
    name="SCANNER_MAX_READ",
    editable=False,
    default=2097152,
)

register_setting(
    name="SCANNER_TIMEOUT",
    editable=False,
    default=20,
)

register_setting(
    name="SCANNER_USER_AGENT",
    editable=False,
    default='firefox',
)

register_setting(
    name="SCANNER_YOUTUBE_EXTRA_ATTR",
    editable=False,
    default=True,
)

register_setting(
    name="UNKNOWN_USERNAME",
    editable=False,
    default='unknown',
)

register_setting(
    name="UPDATER_INTERVAL",
    editable=False,
    default=300,
)
