#!/usr/bin/env python

"""Heuristically programmed ALgorithmic Computer"""

from __future__ import with_statement
import sys
import os
import re
import random
import time
import math
from optparse import OptionParser
import warnings
warnings.simplefilter('ignore')
from sqlobject import *

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = ['HAL']

# defaults
RESET = False
DEBUG = False
ORDER = 5
TIMEOUT = 1

class Dictionary(SQLObject):

    word = BLOBCol(sqlType='TINYBLOB')

    @classmethod
    def add_word(cls, word):
        found = cls.find_word(word)
        if found:
            return found
        else:
            return Words(word=word)

    @classmethod
    def find_word(cls, word):
        rs = list(Words.select(Words.q.word == word))
        if rs:
            return rs[0]


class Words(Dictionary):

    pass


class Tree(SQLObject):

    word = ForeignKey('Words')
    used = IntCol(default=0)
    count = IntCol(default=0)
    parent = IntCol(default=None)

    @property
    def tree(self):
        return list(self.select(self.q.parent == self))

    def add_word(self, word):
        node = self.find_word(word, add=True)
        node.count += 1
        self.used += 1
        return node

    def find_word(self, word, add=False):
        found = list(self.select(AND(self.q.parent == self,
                                     self.q.word == word)))
        if found:
            return found[0]
        elif add:
            return self.__class__(word=word, parent=self.id)


class Forward(Tree):

    pass


class Backward(Tree):

    pass


class HAL(object):

    """Heuristically programmed ALgorithmic Computer"""

    comment_re = re.compile(r'#.*$')

    def __init__(self, timeout=TIMEOUT, order=ORDER, reset=RESET, debug=DEBUG):
        self.timeout = timeout
        self.order = order

        #if os.path.exists(self.train_file):
        #    for line in self.readlines(self.train_file):
        #        self.teach(line)
        #self.ban = self.read_list(self.ban_file)
        #self.aux = self.read_list(self.aux_file)
        #self.swp = []
        #if os.path.exists(self.swap_file):
        #    for line in self.readlines(self.swap_file):
        #        swap = line.split(None, 1)
        #        if len(swap) == 2:
        #            self.swp.append(swap)

        # initialize connection
        #url = 'mysql://user:pass@host:port/dbname'
        #url = 'sqlite:///path/to/file'
        url = 'mysql://tree:tree@localhost:3306/tree'
        sqlhub.processConnection = connectionForURI(url)

        # test debugging
        if debug:
            Words._connection.debug = True
            Forward._connection.debug = True
            Backward._connection.debug = True

        # drop tables
        if reset:
            Words.dropTable(ifExists=True)
            Forward.dropTable(ifExists=True)
            Backward.dropTable(ifExists=True)

        # create tables
        Words.createTable(ifNotExists=True)
        Forward.createTable(ifNotExists=True)
        Backward.createTable(ifNotExists=True)

        # initialize model if new
        if reset:
            word = Words(word='<ERROR>')
            Forward(word=word)
            Backward(word=word)
            Words(word='<FIN>')

        # root nodes
        self.forward = Forward.get(1)
        self.backward = Backward.get(1)

        # table.byCol(val)
        # table(col=val)
        # table.select(table.q.col == val)
        # SQLObjectNotFound
        # val = table.foreign.col
        # table.foreign.col = val

    def initialize_context(self, node):
        self.context = [node] + [None] * (self.order + 1)

    def update_context(self, symbol):
        for i in xrange(self.order + 1, 0, -1):
            if self.context[i - 1] is not None:
                self.context[i] = self.context[i - 1].find_word(symbol)

    # PUBLIC FUNCTIONS

    def process(self, input):
        words = self.make_words(input)
        self.learn(words)
        return self.generate_reply(words).capitalize()

    def teach(self, input):
        self.learn(self.make_words(input))

    # REPLY GENERATION

    def generate_reply(self, words):
        keywords = self.make_keywords(words)
        max_surprise = -1.0
        basetime = time.time()
        output = ''
        while time.time() - basetime < self.timeout:
            replywords = self.reply(keywords)
            surprise = self.evaluate_reply(keywords, replywords)
            print surprise
            if surprise > max_surprise:
                max_surprise = surprise
                output = ''.join(word.word for word in replywords)
        return output

    def evaluate_reply(self, keys, words):
        entropy = 0.0
        num = 0
        if not words:
            return entropy
        self.initialize_context(self.forward)

        for word in words:
            if word.word in keys:
                probability = 0.0
                count = 0
                num += 1
                for j in xrange(self.order):
                    if self.context[j] is not None:
                        node = self.context[j].find_word(word)
                        if node:
                            probability += (float(node.count) /
                                            self.context[j].used)
                            count += 1
                if count:
                    entropy -= math.log(probability / count)
            self.update_context(word)

        self.initialize_context(self.backward)
        for word in reversed(words):
            if word.word in keys:
                probability = 0.0
                count = 0
                num += 1
                for j in xrange(self.order):
                    if self.context[j] is not None:
                        node = self.context[j].find_word(word)
                        if node:
                            probability += (float(node.count) /
                                            self.context[j].used)
                            count += 1
                if count > 0.0:
                    entropy -= math.log(probability / count)
            self.update_context(word)

        if num >= 8:
            entropy /= math.sqrt(num - 1)
        if num >= 16:
            entropy /= num
        return entropy

    def reply(self, keys):
        start = True
        replies = []
        self.initialize_context(self.forward)
        used_key = False
        while True:
            if start:
                word = self.seed(keys)
                start = False
            else:
                word, used_key = self.babble(keys, replies, used_key)
            if word.word in ('<ERROR>', '<FIN>'):
                break
            replies.append(word)
            self.update_context(word)

        self.initialize_context(self.backward)

        if replies:
            for i in xrange(min(len(replies) - 1, self.order), -1, -1):
                word = Words.find_word(replies[i])
                self.update_context(word)

        while True:
            word, used_key = self.babble(keys, replies, used_key)
            if word.word in ('<ERROR>', '<FIN>'):
                break
            replies.insert(0, word)
            self.update_context(word)
        return replies

    def babble(self, keys, words, used_key):
        word = Words.get(1)
        node = None
        for i in xrange(0, self.order + 1):
            if self.context[i]:
                node = self.context[i]
        if not node or not node.tree:
            return word, used_key
        branch = random.choice(node.tree)
        count = random.randrange(node.used)
        while count >= 0:
            word = branch.word
            if word.word in keys and word.word not in words:
                # XXX and (used_key or word.word not in aux
                used_key = True
                break
            count -= branch.count
            if i >= len(node.tree) - 1:
                i = 0
            else:
                i += 1
        return word, used_key

    def seed(self, keys):
        if not self.context[0]:
            word = Words.get(1)
        else:
            word = random.choice(self.context[0].tree).word
        if keys:
            i = random.randrange(len(keys))
            keys = keys[i:] + keys[:i]
            for test_word in keys:
                found = Words.find_word(test_word)
                if found:  # XXX and not in aux
                    return found
        return word

    def make_keywords(self, words):
        return words
        # XXX predicated on swap, aux and ban
        # keys = []
        # for word in words:
        #     c = 0
        #     for search, replace in self.swp:
        #         if search == word:
        #             self.add_key(keys, replace)
        #             c += 1
        #     if c == 0:
        #         self.add_key(keys, word)

        # if keys:
        #     for word in words:
        #         c = 0
        #         for search, replace in self.swp:
        #             if search == word:
        #                 self.add_aux(keys, replace)
        #                 c += 1
        #         if c == 0:
        #             self.add_aux(keys, word)

        # return keys

    # def add_key(self, keys, word):
    #     if (Words.find_word(word) and
    #         word[0].isalnum() and
    #         not self.ban.find_word(word) and
    #         not self.aux.find_word(word)):
    #         keys.add_word(word)

    # def add_aux(self, keys, word):
    #     if (Words.find_word(word) and
    #         word[0].isalnum() and
    #         not self.aux.find_word(word)):
    #         keys.add_word(word)

    # LEARNING FUNCTIONS

    def learn(self, words):
        if len(words) <= self.order:
            return
        self.initialize_context(self.forward)
        for word in words:
            self.update_model(Words.add_word(word))
        self.update_model(1)
        self.initialize_context(self.backward)
        for word in reversed(words):
            symbol = Words.find_word(word)
            self.update_model(symbol)
        self.update_model(1)

    def update_model(self, symbol):
        for i in xrange(self.order + 1, 0, -1):
            if self.context[i - 1]:
                node = self.context[i - 1].add_word(symbol)
                self.context[i] = node

    # UTILITY FUNCTIONS

    def make_words(self, input):
        offset = 0
        words = []
        if not input:
            return words
        input = input.lower()
        while True:
            if self.boundary(input, offset):
                words.append(input[:offset])
                if offset == len(input):
                    break
                input = input[offset:]
                offset = 0
            else:
                offset += 1
        if words[-1][0].isalnum():
            words.append('.')
        elif words[-1][-1] not in '!.?':
            words[-1] = '.'
        return words

    @classmethod
    def readlines(cls, path):
        with open(path, 'r') as file:
            for line in file:
                yield cls.comment_re.sub('', line).strip()

    @classmethod
    def read_list(cls, path):
        words = Dictionary()
        if path and os.path.exists(path):
            for line in cls.readlines(path):
                for word in line.split():
                    if word:
                        words.add_word(word)
        return words

    @staticmethod
    def boundary(string, position):
        if position == 0:
            return False
        if position == len(string):
            return True
        if ((len(string) - position > 1) and
            (string[position] == "'") and
            (string[position - 1].isalpha()) and
            (string[position + 1].isalpha())):
            return False
        if ((position > 1) and
            (string[position - 1] == "'") and
            (string[position - 2].isalpha()) and
            (string[position].isalpha())):
            return False
        if ((string[position].isalpha()) and
            (not string[position - 1].isalpha())):
            return True
        if ((not string[position].isalpha()) and
            (string[position - 1].isalpha())):
            return True
        if string[position].isdigit() != string[position - 1].isdigit():
            return True
        return False


def main():
    """Parse args and create a simple chat bot"""
    parser = OptionParser(version=__version__)
    toggle = lambda x: ('store_%s' % (not x)).lower()
    parser.add_option('-r', '--reset', default=RESET, action=toggle(RESET),
                      help='reset database (%default)')
    parser.add_option('-d', '--debug', default=DEBUG, action=toggle(DEBUG),
                      help='show SQL statements (%default)')
    parser.add_option('-t', '--timeout', metavar='<seconds>', default=TIMEOUT,
                      type='float', help='search time for replies (%default)')
    parser.add_option('-o', '--order', metavar='<int>', default=ORDER,
                      type='int', help='size of contexts (%default)')
    opts, args = parser.parse_args()
    if args:
        parser.error('invalid args')

    hal = HAL(**opts.__dict__)

    try:
        while True:
            input = raw_input('>>> ').strip().lower()
            if not input:
                continue
            if input == '#quit':
                break
            else:
                print hal.process(input)
    except (EOFError, KeyboardInterrupt):
        print
    return 0


if __name__ == '__main__':
    sys.exit(main())
