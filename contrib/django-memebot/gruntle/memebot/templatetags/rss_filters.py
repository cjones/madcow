"""Custom text filters"""

from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.conf import settings
from django import template
from gruntle.memebot.utils import text

register = template.Library()

@register.filter(name='summarize')
@stringfilter
def summarize(value, size=None, cont=None):
    """Truncates the text to the specified size"""
    if size is None:
        size = settings.FEED_SUMMARY_SIZE
    if cont is None:
        cont = settings.FEED_SUMMARY_CONT
    size -= len(cont)
    value = text.sdecode(value)
    if value is not None:
        words = value[:size].split()
        if len(value) > size:
            words[-1] = cont
        value = mark_safe(u' '.join(words))
    return value


@register.tag(name='rss_url')
def rss_url(*args, **kwargs):
    from django.template.defaulttags import url as reverse_url, URLNode as BaseURLNode
    from urlparse import urljoin

    node = reverse_url(*args, **kwargs)

    class URLNode(BaseURLNode):

        def __init__(self):
            pass

        def __getattribute__(self, key):
            try:
                return super(URLNode, self).__getattribute__(key)
            except AttributeError:
                return getattr(node, key)

        def render(self, *args, **kwargs):
            url = node.render(*args, **kwargs)
            return urljoin(settings.FEED_BASE_URL, url)

    return URLNode()
