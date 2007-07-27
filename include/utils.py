#!/usr/bin/env python

# Some helper functions

import xml.sax.saxutils
import re

re_nbsp = re.compile('&nbsp;', re.I)
re_br   = re.compile('<br[^>]+>', re.I)
re_middot = re.compile('&middot;', re.I)
re_quot = re.compile('&quot;', re.I)
re_tags = re.compile('<[^>]+>')
re_newlines = re.compile('[\r\n]+')

entityNameMap = {'frac14': 188, 'icirc': 238, 'cedil': 184, 'acute': 180, 'plusmn': 177, 'eth': 240, 'aelig': 230, 'yen': 165, 'quot': 34, 'shy': 173, 'macr': 175, 'ordm': 186, 'ouml': 246, 'times': 215, 'agrave': 224, 'para': 182, 'reg': 174, 'sup2': 178, 'sup1': 185, 'ordf': 170, 'euml': 235, 'frac34': 190, 'iuml': 239, 'ugrave': 249, 'sup3': 179, 'nbsp': 32, 'lt': 60, 'brvbar': 166, 'micro': 181, 'eacute': 233, 'ntilde': 241, 'copy': 169, 'pound': 163, 'curren': 164, 'oacute': 243, 'egrave': 232, 'deg': 176, 'thorn': 254, 'middot': 183, 'igrave': 236, 'ocirc': 244, 'raquo': 187, 'ograve': 242, 'amp': 38, 'uuml': 252, 'iquest': 191, 'gt': 62, 'uacute': 250, 'ecirc': 234, 'oslash': 248, 'aacute': 225, 'atilde': 227, 'sect': 167, 'yacute': 253, 'iacute': 205, 'cent': 162, 'auml': 228, 'not': 172, 'uml': 168, 'aring': 229, 'frac12': 189, 'ucirc': 251, 'szlig': 223, 'acirc': 226, 'ccedil': 231, 'otilde': 245, 'divide': 247, 'iexcl': 161}

reEntity = re.compile('&(#\d{1,3}|\w{1,8});', re.I)
reValue = re.compile('^#(\d+)$')

def convertEntities(text):
	for entity in reEntity.findall(text):
		try: val = entityNameMap[entity.lower()]
		except:
			try: val = int(reValue.search(entity).group(1))
			except: continue

		if val < 256: char = chr(val)
		else: char = ' '

		text = re.sub('&' + entity + ';', char, text)

	return text

def stripHTML(data = None):
    data = re_tags.sub('', data)
    data = xml.sax.saxutils.unescape(data)
    data = re_nbsp.sub('', data)
    data = re_br.sub('\n', data)
    data = re_middot.sub('-', data)
    data = re_quot.sub("'", data)
    data = re_newlines.sub('\n', data)
    data = convertEntities(data)
    return data

re_highascii = re.compile('([\x80-\xff])')

def isUTF8(data = None, threshold = .25):
    if (float(len(re_highascii.findall(data))) / float(len(data))) > threshold:
        return True
    else:
        return False


