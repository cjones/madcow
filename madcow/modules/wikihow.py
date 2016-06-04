# vim:ft=python:sw=4:sts=4:ts=8:tw=0:et:sta
# ported from https://raw.githubusercontent.com/EArmour/pyfibot/master/pyfibot/modules/module_wikihow.py

from madcow.util import Module
from madcow.util.text import decode
import random
import re
import os

_notrap = SystemExit, KeyboardInterrupt

class Main(Module):

    pattern = re.compile(r'^\s*(?:how\s+do\s+i\s+.+|how(?:to)?(?:\s+(\d+))?)\s*$', re.I)
    help = 'how[to] [#] - get random wikihow mashup\nhow do i <ignores rest..> - alternate wikihow syntax'

    def response(self, nick, args, kwargs):
        try:
            count = int(args[0])
            if count < 1 or count > 11:
                raise ValueError
        except _notrap:
            raise
        except:
            count = 3
        try:
            results = self.getrandom(times=count)
        except _notrap:
            raise
        except:
            import traceback
            traceback.print_exc()
            results = ['i has an aerror when wikihowing. it may be down, who knows.']
        return os.linesep.join('{}: {}'.format(nick, line) for line in results if line)

    def getrandom(self, times=3):
        """".how (times) - Gives you random instructions from wikiHow, by default 3 steps"""
        steps = []
        for i in xrange(times):
            page = self.getsoup("http://www.wikihow.com/Special:Randomizer")
            section = page.find("div", {"id": "steps"})
            if section: # Only one 'method'
                allsteps = section.find("ol").findChildren("li", recursive=False)
            else: # Multiple 'methods', each with their own list of steps
                for x in xrange(1, 5):
                    try:
                        section  = page.find("div", {"id": "steps_{}".format(x)})
                        try:
                            # Possible for a Method to have no actual steps, just a paragraph, so check for the list
                            allsteps = section.find("ol").findChildren("li", recursive=False)
                            break
                        except _notrap:
                            raise
                        except:
                            continue
                    except _notrap:
                        raise
                    except:
                        break

            steps.append(random.choice(allsteps))

        results = []
        for i, step in enumerate(steps):
            tag = step.find("b", {"class": "whb"})
            results.append(u'Step #{}: {}'.format(i + 1, decode(tag.text)))
        return results
