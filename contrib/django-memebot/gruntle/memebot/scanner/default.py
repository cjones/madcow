"""Should be called last, if nothing can do a better job with the URL"""

from gruntle.memebot.scanner import Scanner, ScanResult

class DefaultScanner(Scanner):

    def handle(self, response, log):
        return ScanResult(response, None, None, None, None)


scanner = DefaultScanner()
