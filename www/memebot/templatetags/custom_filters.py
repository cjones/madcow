from django import template
from django.utils.html import escape

register = template.Library()

@register.filter("safelink")
def safelink(url, limit=None):
	url = str(url)
	size = len(url)
	url = escape(url)

	link = '<a href="%s" target="_new">' % url

	if limit is not None and size > limit:
		url = url[:limit] + '...' + url[-4:]

	return '%s%s</a>' % (link, url)
