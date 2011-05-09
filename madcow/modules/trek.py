"""Star Trek failure generator"""

from BeautifulSoup import BeautifulSoup
from madcow.util.http import geturl
from madcow.util import strip_html, Module
import re

class Main(Module):

    pattern = re.compile(r'^\s*(?:star\s*)?trek\s*$', re.I)
    help = u'startrek - generate technobabble'
    url = 'http://hyotynen.kapsi.fi/trekfailure/'
    fail_re = re.compile(r'^[ \n]*- (.*?) -[ \n]*$')
    spaces_re = re.compile(r'\s{2,}')
    error = u'Too much fail for technobabble'

    def init(self):
        self.col = self.madcow.colorlib.get_color

    def response(self, nick, args, kwargs):
        fail = BeautifulSoup(geturl(self.url)).h1
        return self.spaces_re.sub(' ', strip_html(
            u'%s: %s: %s %s: %s' % (
                nick, self.col('red', text='FAIL'),
                self.fail_re.search(fail.renderContents()).group(1),
                self.col('green', text='FIX'),
                self.fail_re.search(fail.findNext('h1').renderContents()).group(1))))
