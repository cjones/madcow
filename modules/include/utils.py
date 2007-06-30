#!/usr/bin/env python

"""
$Id: utils.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Some helper functions
"""

import xml.sax.saxutils
import re

re_nbsp = re.compile('&nbsp;', re.I)
re_br   = re.compile('<br[^>]+>', re.I)
re_middot = re.compile('&middot;', re.I)
re_quot = re.compile('&quot;', re.I)
re_tags = re.compile('<[^>]+>')
re_newlines = re.compile('[\r\n]+')

def stripHTML(data = None):
	data = re_tags.sub('', data)
	data = xml.sax.saxutils.unescape(data)
	data = re_nbsp.sub('', data)
	data = re_br.sub('\n', data)
	data = re_middot.sub('-', data)
	data = re_quot.sub("'", data)
	data = re_newlines.sub('\n', data)
	return data

re_highascii = re.compile('([\x80-\xff])')

def isUTF8(data = None, threshold = .25):
	if (float(len(re_highascii.findall(data))) / float(len(data))) > threshold:
		return True
	else:
		return False


