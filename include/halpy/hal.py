#!/usr/bin/env python
#
# Copyright (c) 2008, Chris Jones
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Heuristically programmed ALgorithmic Computer"""

from __future__ import with_statement, division
from optparse import OptionParser
import sys
import re
import random
import math
import time
import tables
import os

# metadata
__version__ = '0.4'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__usage__ = '%prog [options] [training file, ...]'
__all__ = ['HAL']

# defaults
FILENAME = os.path.expanduser('~/.haldb')  # default database file
INTERACTIVE = True      # speak interactively to bot
RESET = False           # resets database
NOLEARN = False         # refuse to learn while speaking interactively
TIMEOUT = 1             # how long to look for replies
ORDER = 5               # markov order. not recommended to change from 5
MAX_WORD_SIZE = 32      # maximum size a word can be

# hard-code list of words for BAN/SWAP/AUX table.. no need to change these

AUX_WORDS = ('dislike', 'he', 'her', 'hers', 'him', 'his', 'i', "i'd", "i'll",
             "i'm", "i've", 'like', 'me', 'mine', 'my', 'myself', 'one',
             'she', 'three', 'two', 'you', "you'd", "you'll", "you're",
             "you've", 'your', 'yours', 'yourself')

BAN_WORDS = ('a', 'ability', 'able', 'about', 'absolute', 'absolutely',
             'across', 'actual', 'actually', 'after', 'afternoon', 'again',
             'against', 'ago', 'agree', 'all', 'almost', 'along', 'already',
             'although', 'always', 'am', 'an', 'and', 'another', 'any',
             'anyhow', 'anything', 'anyway', 'are', "aren't", 'around', 'as',
             'at', 'away', 'back', 'bad', 'be', 'been', 'before', 'behind',
             'being', 'believe', 'belong', 'best', 'better', 'between', 'big',
             'bigger', 'biggest', 'bit', 'both', 'buddy', 'but', 'by', 'call',
             'called', 'calling', 'came', 'can', "can't", 'cannot', 'care',
             'caring', 'case', 'catch', 'caught', 'certain', 'certainly',
             'change', 'close', 'closer', 'come', 'coming', 'common',
             'constant', 'constantly', 'could', 'current', 'day', 'days',
             'derived', 'describe', 'describes', 'determine', 'determines',
             'did', "didn't" 'do', 'does', "doesn't", 'doing', "don't", 'done',
             'doubt', 'down', 'each', 'earlier', 'early', 'else', 'enjoy',
             'especially', 'even', 'ever', 'every', 'everybody', 'everyone',
             'everything', 'fact', 'fair', 'fairly', 'far', 'fellow', 'few',
             'find', 'fine', 'for', 'form', 'found', 'from', 'full', 'further',
             'gave', 'get', 'getting', 'give', 'given', 'giving', 'go',
             'going', 'gone', 'good', 'got', 'gotten', 'great', 'had', 'has',
             "hasn't", 'have', "haven't", 'having', 'held', 'here', 'high',
             'hold', 'holding', 'how', 'if', 'in', 'indeed', 'inside',
             'instead', 'into', 'is', "isn't", 'it', "it's", 'its', 'just',
             'keep', 'kind', 'knew', 'know', 'known', 'large', 'larger',
             'largets', 'last', 'late', 'later', 'least', 'less', 'let',
             "let's", 'level', 'likes', 'little', 'long', 'longer', 'look',
             'looked', 'looking', 'looks', 'low', 'made', 'make', 'making',
             'many', 'mate', 'may', 'maybe', 'mean', 'meet', 'mention',
             'mere', 'might', 'moment', 'more', 'morning', 'most', 'move',
             'much', 'must', 'near', 'nearer', 'never', 'next', 'nice',
             'nobody', 'none', 'noon', 'noone', 'not', 'note', 'nothing',
             'now', 'obvious', 'of', 'off', 'on', 'once', 'only', 'onto',
             'opinion', 'or', 'other', 'our', 'out', 'over', 'own', 'part',
             'particular', 'particularly', 'perhaps', 'person', 'piece',
             'place', 'pleasant', 'please', 'popular', 'prefer', 'pretty',
             'put', 'quite', 'real', 'really', 'receive', 'received', 'recent',
             'recently', 'related', 'result', 'resulting', 'results', 'said',
             'same', 'saw', 'say', 'saying', 'see', 'seem', 'seemed', 'seems',
             'seen', 'seldom', 'sense', 'set', 'several', 'shall', 'short',
             'shorter', 'should', 'show', 'shows', 'simple', 'simply',
             'small', 'so', 'some', 'someone', 'something', 'sometime',
             'sometimes', 'somewhere', 'sort', 'sorts', 'spend', 'spent',
             'still', 'stuff', 'such', 'suggest', 'suggestion', 'suppose',
             'sure', 'surely', 'surround', 'surrounds', 'take', 'taken',
             'taking', 'tell', 'than', 'thank', 'thanks', 'that', "that's",
             'thats', 'the', 'their', 'them', 'then', 'there', 'therefore',
             'these', 'they', 'thing', 'things', 'this', 'those', 'though',
             'thoughts', 'thouroughly', 'through', 'tiny', 'to', 'today',
             'together', 'told', 'tomorrow', 'too', 'total', 'totally',
             'touch', 'try', 'twice', 'under', 'understand', 'understood',
             'until', 'up', 'us', 'used', 'using', 'usually', 'various',
             'very', 'want', 'wanted', 'wants', 'was', 'watch', 'way', 'ways',
             'we', "we're", 'well', 'went', 'were', 'what', "what's",
             'whatever', 'whats', 'when', 'where', "where's" 'which', 'while',
             'whilst', 'who', "who's", 'whom', 'will', 'wish', 'with',
             'within', 'wonder', 'wonderful', 'worse', 'worst', 'would',
             'wrong', 'yesterday', 'yet')

SWAP_WORDS = {'dislike': 'like', 'hate': 'love', 'i': 'you', "i'd": "you'd",
              "i'll": "you'll", "i'm": "you're", "i've": "you've",
              'like': 'dislike', 'love': 'hate', 'me': 'you', 'mine': 'yours',
              'my': 'your', 'myself': 'yourself', 'no': 'yes',
              'why': 'because', 'yes': 'no', 'you': 'i', 'you': 'me',
              "you'd": "i'd", "you'll": "i'll", "you're": "i'm",
              "you've": "i've", 'your': 'my', 'yours': 'mine',
              'yourself': 'myself'}

class Words(tables.IsDescription):

    id = tables.UInt32Col()
    string = tables.StringCol(MAX_WORD_SIZE)


class ProgressMeter(object):

    """Context that calculates remaining time of an operation"""

    units = [('second', 60),
             ('minute', 60),
             ('hour', 24),
             ('day', 7),
             ('week', 4),
             ('month', 12),
             ('year', 0)]

    def __init__(self, size):
        self.size = size
        self.times = []
        self.count = 0
        self.last = 0
        self.begin = self.start = time.time()

    def __enter__(self):
        self.start = time.time()
        self.update(1)

    def __exit__(self, *args):
        self.times.append(self.operation_elapsed)
        status = self.get_status()
        sys.stdout.write('\r' + ' ' * self.last)
        sys.stdout.write('\r' + status)
        sys.stdout.flush()
        self.last = len(status)

    def update(self, n):
        self.count += n

    @property
    def operation_elapsed(self):
        return time.time() - self.start

    @property
    def elapsed(self):
        return self.readable_time(time.time() - self.begin)

    def get_status(self):
        return '[%d/%d] %.2f%% (%s)' % (
                self.count,
                self.size,
                (self.count / self.size * 100),
                self.readable_time(self.left * self.avg))

    @property
    def left(self):
        return self.size - self.count

    @property
    def avg(self):
        return sum(self.times) / len(self.times)

    @classmethod
    def readable_time(cls, seconds):
        """Convert arbitrary number of seconds into human readable format"""
        units = []
        for unit, size in cls.units:
            seconds = int(seconds)
            if size and seconds >= size:
                remainder = seconds % size
                seconds = seconds / size
            else:
                remainder = seconds
                seconds = 0
            if remainder:
                if remainder > 1:
                    unit += 's'
                units.append('%s %s' % (remainder, unit))
            if not seconds:
                break
        return ' '.join(reversed(units))


class HAL(object):

    """Heuristically programmed ALgorithmic Computer"""

    boundary_re = re.compile(r"(\s+|[^a-z0-9']+)")
    endpunc = ('.', '!', '?')

    def __init__(self, filename=FILENAME, reset=RESET, nolearn=NOLEARN,
                 timeout=TIMEOUT, order=ORDER):

        """Initialize HAL brain"""

        self.order = order
        self.nolearn = nolearn
        self.timeout = timeout
        if not os.path.exists(filename):
            reset = True
        if reset and os.path.exists(filename):
            os.remove(filename)
        self.db = tables.openFile(filename, mode='a')
        root = self.db.root

        # initialize a new database
        if reset:
            words = self.db.createTable(root, 'words', Words)
            words.row['id'] = 1
            words.row['string'] = '<ROOT>'
            words.row.append()
            words.row['id'] = 2
            words.row['string'] = '<FIN>'
            words.row.append()
            words.attrs.next = 3
            words.flush()
            forward = self.db.createGroup(root, 'forward')
            forward._v_attrs.used = 0
            forward._v_attrs.count = 0
            forward._v_attrs.word = 1
            backward = self.db.createGroup(root, 'backward')
            backward._v_attrs.used = 0
            backward._v_attrs.count = 0
            backward._v_attrs.word = 1
            self.db.flush()
        self.forward = root.forward
        self.backward = root.backward
        self.words = root.words

        # keep words in memory, doesn't take much room.. keeps
        # a dictionary for loooking up in both directions quickly
        self.words_id = {}
        self.words_string = {}
        for word in self.words:
            self.words_id[word['id']] = word['string']
            self.words_string[word['string']] = word['id']

    def train(self, path):
        """Train HAL from file (one sentence per line)"""
        with open(path, 'r') as fp:
            total = 0
            for line in fp:
                total += 1
            fp.seek(0)
            meter = ProgressMeter(total)
            try:
                for line in fp:
                    with meter:
                        self.process(line, reply=False, learn=True)
            finally:
                print '\nElapsed: %s' % meter.elapsed

    def process(self, line, learn=True, reply=True):
        """Process a line of input"""
        line = line.strip()
        line = line.lower()
        strings = self.boundary_re.split(line)
        strings = [string.replace(' ', '<SPACE>')
                   for string in strings if string]
        if not strings:
            return
        if strings[-1][-1] not in self.endpunc:
            strings.append('.')
        if learn and not self.nolearn:
            self._learn(strings)
        if reply:
            return self._reply(strings)

    def interact(self):
        """Speak interactively to HAL until EOF/break"""
        while True:
            line = raw_input('>>> ')
            if line:
                print self.process(line)

    # the rest of these functions are internal

    def _learn(self, strings):
        """Learn from user input"""
        if len(strings) <= self.order:
            return
        self._init(self.forward)
        for string in strings:
            if string in self.words_string:
                word_id = self.words_string[string]
            else:
                # add new word and update cache
                word = self.words.row
                word_id = self.words.attrs.next
                word['id'] = word_id
                word['string'] = string
                word.append()
                self.words.attrs.next += 1
                self.words_string[string] = word_id
                self.words_id[word_id] = string
            self._update(word_id, add=True)
        self._update(2, add=True)  # add sentence terminator <FIN>

        # update backward model
        self._init(self.backward)
        for string in reversed(strings):
            self._update(self.words_string[string], add=True)
        self._update(2, add=True)  # add sentence terminator <FIN>
        self.db.flush()

    def _reply(self, strings):
        """Generate a reply based off of user input"""

        # generate keywords
        keys = []
        for string in strings:
            if string in SWAP_WORDS:
                string = SWAP_WORDS[string]
            if (string in self.words_string and string[0].isalnum() and
                string not in BAN_WORDS and string not in AUX_WORDS):
                keys.append(string)
        if keys:
            for string in strings:
                if string in SWAP_WORDS:
                    string = SWAP_WORDS[string]
                if (string in self.words_string and
                    string[0].isalnum() and
                    string in AUX_WORDS):
                    keys.append(string)

        # generate replies in time window, using reply with highest entropy
        max_surprise = -1.0
        basetime = time.time()
        output = None
        count = 0
        while time.time() - basetime < self.timeout:
            count += 1
            reply = []
            start = True
            self._init(self.forward)
            used_key = False
            while True:
                if start:
                    word_id = self._seed(keys)
                    start = False
                else:
                    word_id, used_key = self._babble(keys, reply, used_key)
                if word_id < 3:
                    break
                reply.append(self.words_id[word_id])
                self._update(word_id, add=False)
            self._init(self.backward)
            if reply:
                for i in xrange(min(len(reply) - 1, self.order), -1, -1):
                    self._update(self.words_string[reply[i]], add=False)
            while True:
                word_id, used_key = self._babble(keys, reply, used_key)
                if word_id < 3:
                    break
                reply.insert(0, self.words_id[word_id])
                self._update(word_id, add=False)
            surprise = self._evaluate_reply(keys, reply)
            if surprise > max_surprise:
                max_surprise = surprise
                output = reply
        self.db.flush()
        if output:
            return ''.join(output).replace('<SPACE>', ' ').capitalize()
        else:
            return 'I am utterly speechless!'

    def _seed(self, keys):
        """Get first word in reply"""
        if keys:
            i = random.randrange(len(keys))
            for string in keys[i:] + keys[:i]:
                if string in self.words_string and string not in AUX_WORDS:
                    return self.words_string[string]
        tree = [child for child in self.context[0]]
        if tree:
            return random.choice(tree)._v_attrs.word
        return 1

    def _babble(self, keys, reply, used_key):
        """Get next word in reply"""
        word_id = 1
        for i in xrange(self.order + 1):
            if self.context[i] is not None:
                node = self.context[i]
        tree = [child for child in node]
        if not tree:
            return word_id, used_key
        i = random.randrange(len(tree))
        count = random.randrange(node._v_attrs.used)
        while count >= 0:
            child = tree[i]
            word_id = child._v_attrs.word
            string = self.words_id[word_id]
            if ((string in keys) and
                (used_key or (string not in AUX_WORDS)) and
                (string not in reply)):
                used_key = True
                break
            count -= child._v_attrs.count
            if i >= len(tree) - 1:
                i = 0
            else:
                i = i + 1
        return word_id, used_key

    def _evaluate_reply(self, keys, reply):
        """Calculate difference between question and reply"""
        num, entropy = self._calc_entropy(self.forward, reply, keys)
        num, entropy = self._calc_entropy(self.backward, reversed(reply),
                                          keys, num, entropy)
        if num >= 8:
            entropy /= math.sqrt(num - 1)
        if num >= 16:
            entropy /= num
        return entropy

    def _calc_entropy(self, root, strings, keys, num=0, entropy=0.0):
        """Calculate entropy"""
        self._init(root)
        for string in strings:
            word_id = self.words_string[string]
            if string in keys:
                prob = 0.0
                count = 0
                num += 1
                for i in xrange(self.order):
                    node = self.context[i]
                    if node and node._v_attrs.used:
                        child = getattr(node, 'word%s' % word_id)
                        prob += child._v_attrs.count / node._v_attrs.used
                        count += 1
                if count:
                    entropy -= math.log(prob / count)
            self._update(word_id, add=False)
        return num, entropy

    def _init(self, node):
        """Initialize markov model"""
        self.context = [node] + [None] * (self.order + 1)

    def _update(self, word_id, add=False):
        """Update markov model with word"""
        for i in xrange(self.order + 1, 0, -1):
            if self.context[i - 1]:
                node = self.context[i - 1]
                try:
                    child = getattr(node, 'word%s' % word_id)
                except tables.NoSuchNodeError:
                    if add:
                        child = self.db.createGroup(node, 'word%s' % word_id)
                        child._v_attrs.used = 0
                        child._v_attrs.count = 0
                        child._v_attrs.word = word_id
                    else:
                        child = self.forward
                self.context[i] = child
                if add:
                    child._v_attrs.count += 1
                    node._v_attrs.used += 1


def main():
    parser = OptionParser(version=__version__, usage=__usage__)
    toggle = lambda bool: ('store_%s' % (not bool)).lower()
    parser.add_option('-f', dest='filename', metavar='<path>',
                      default=FILENAME, help='data file (default: %default)')
    parser.add_option('-i', dest='interactive', default=INTERACTIVE,
                      action=toggle(INTERACTIVE),
                      help='run interactively (default: %default)')
    parser.add_option('-n', dest='nolearn', default=NOLEARN,
                      action=toggle(NOLEARN),
                      help="don't learn from interaction (default: %default)")
    parser.add_option('-r', dest='reset', default=RESET, action=toggle(RESET),
                      help='reset database (default: %default)')
    parser.add_option('-t', dest='timeout', metavar='<secs>', default=TIMEOUT,
                      type='float',
                      help='time to search for a reply (default: %default)')
    parser.add_option('-o', dest='order', metavar='<int>', default=ORDER,
                      type='int', help='markov order (default: %default)')
    opts, args = parser.parse_args()
    interactive = opts.interactive
    del opts.interactive
    hal = None
    try:
        hal = HAL(**opts.__dict__)
        for path in args:
            hal.train(path)
        if interactive:
            hal.interact()
    except (EOFError, KeyboardInterrupt):
        print
    except tables.NoSuchNodeError:
        parser.error('missing tables, try running with -r')
    finally:
        if hal:
            hal.db.close()
    return 0


if __name__ == '__main__':
    try:
        import psyco
        psyco.cannotcompile(re.compile)
        psyco.full()
    except ImportError:
        pass
    sys.exit(main())

