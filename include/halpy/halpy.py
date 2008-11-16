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
import cPickle as pickle

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = ['HAL']

# defaults
DIRECTORY = './db'
ORDER = 5
TIMEOUT = 1

class Dictionary(list):

    """Array extended with some helper functions"""

    __slots__ = []

    def add_word(self, word):
        if word not in self:
            self.append(word)
        return self.index(word)

    def find_word(self, word):
        if word in self:
            return self.index(word)
        return 0


class Tree(object):

    """Tree of word symbols"""

    __slots__ = ['symbol', 'usage', 'count', 'tree']

    def __init__(self, symbol=0):
        self.symbol = symbol
        self.usage = 0
        self.count = 0
        self.tree = []

    def add_symbol(self, symbol):
        node = self.find_symbol(symbol, add=True)
        node.count += 1
        self.usage += 1
        return node

    def find_symbol(self, symbol, add=False):
        i, found = 0, False
        if self.tree:
            min = 0
            max = len(self.tree) - 1
            while True:
                middle = (min + max) / 2
                compar = symbol - self.tree[middle].symbol
                if compar == 0:
                    i, found = middle, True
                    break
                elif compar > 0:
                    if max == middle:
                        i, found = middle + 1, False
                        break
                    min = middle + 1
                else:
                    if min == middle:
                        i, found = middle, False
                        break
                    max = middle - 1
        if found:
            node = self.tree[i]
        elif add:
            node = Tree(symbol)
            self.tree.insert(i, node)
        return node

    # PICKLE INSTRUCTIONS

    def __getstate__(self):
        return self.symbol, self.tree, self.usage, self.count

    def __setstate__(self, state):
        self.symbol, self.tree, self.usage, self.count = state


class Model(object):

    """HAL Data model"""

    __slots__ = ['order', 'forward', 'backward', 'dictionary', 'context']

    def __init__(self, order):
        self.order = order
        self.forward = Tree()
        self.backward = Tree()
        self.initialize_context()
        self.dictionary = Dictionary()
        self.dictionary.add_word('<ERROR>')
        self.dictionary.add_word('<FIN>')

    def initialize_context(self, start=None):
        self.context = [start] + [None] * (self.order + 1)

    def update_context(self, symbol):
        for i in xrange(self.order + 1, 0, -1):
            if self.context[i - 1] is not None:
                self.context[i] = self.context[i - 1].find_symbol(symbol)

    # PICKLE INSTRUCTIONS

    def __getstate__(self):
        return self.order, self.forward, self.backward, self.dictionary

    def __setstate__(self, state):
        self.order, self.forward, self.backward, self.dictionary = state


class HAL(object):

    """Heuristically programmed ALgorithmic Computer"""

    __slots__ = ['directory', 'timeout', 'model', 'ban', 'aux', 'swp']
    comment_re = re.compile(r'#.*$')

    def __init__(self, directory=DIRECTORY, timeout=TIMEOUT, order=ORDER):
        self.directory = directory
        self.timeout = timeout
        self.model = Model(order)
        if os.path.exists(self.brain_file):
            with open(self.brain_file, 'rb') as file:
                try:
                    self.model = pickle.load(file)
                except Exception, error:
                    print >> sys.stderr, 'problem loading brain: %s' % error
        else:
            if os.path.exists(self.train_file):
                for line in self.readlines(self.train_file):
                    self.teach(line)
        self.ban = self.read_list(self.ban_file)
        self.aux = self.read_list(self.aux_file)
        self.swp = []
        if os.path.exists(self.swap_file):
            for line in self.readlines(self.swap_file):
                swap = line.split(None, 1)
                if len(swap) == 2:
                    self.swp.append(swap)

    # PUBLIC FUNCTIONS

    def process(self, input):
        words = self.make_words(input)
        self.learn(words)
        return self.generate_reply(words).capitalize()

    def teach(self, input):
        self.learn(self.make_words(input))

    def save(self):
        with open(self.brain_file, 'wb') as file:
            pickle.dump(self.model, file)

    # REPLY GENERATION

    def generate_reply(self, words):
        keywords = self.make_keywords(words)
        max_surprise = -1.0
        basetime = time.time()
        output = ''
        while time.time() - basetime < self.timeout:
            replywords = self.reply(keywords)
            surprise = self.evaluate_reply(keywords, replywords)
            if surprise > max_surprise:
                max_surprise = surprise
                output = ''.join(replywords)
        return output

    def evaluate_reply(self, keys, words):
        entropy = 0.0
        num = 0
        if not words:
            return entropy
        self.model.initialize_context(self.model.forward)

        for word in words:
            symbol = self.model.dictionary.find_word(word)
            if keys.find_word(word):
                probability = 0.0
                count = 0
                num += 1
                for j in xrange(self.model.order):
                    if self.model.context[j] is not None:
                        node = self.model.context[j].find_symbol(symbol)
                        probability += (float(node.count) /
                                        self.model.context[j].usage)
                        count += 1
                if count:
                    entropy -= math.log(probability / count)
            self.model.update_context(symbol)

        self.model.initialize_context(self.model.backward)
        for word in reversed(words):
            symbol = self.model.dictionary.find_word(word)
            if keys.find_word(word) != 0:
                probability = 0.0
                count = 0
                num += 1
                for j in xrange(self.model.order):
                    if self.model.context[j] is not None:
                        node = self.model.context[j].find_symbol(symbol)
                        probability += (float(node.count) /
                                        self.model.context[j].usage)
                        count += 1
                if count > 0.0:
                    entropy -= math.log(probability / count)
            self.model.update_context(symbol)

        if num >= 8:
            entropy /= math.sqrt(num - 1)
        if num >= 16:
            entropy /= num
        return entropy

    def reply(self, keys):
        start = True
        replies = Dictionary()
        self.model.initialize_context(self.model.forward)
        used_key = False
        while True:
            if start:
                symbol = self.seed(keys)
            else:
                symbol, used_key = self.babble(keys, replies, used_key)
            if symbol == 0 or symbol == 1:
                break
            start = False
            word = self.model.dictionary[symbol]
            replies.append(self.model.dictionary[symbol])
            self.model.update_context(symbol)

        self.model.initialize_context(self.model.backward)
        if replies:
            for i in xrange(min(len(replies) - 1, self.model.order), -1, -1):
                symbol = self.model.dictionary.find_word(replies[i])
                self.model.update_context(symbol)

        while True:
            symbol, used_key = self.babble(keys, replies, used_key)
            if symbol == 0 or symbol == 1:
                break
            word = self.model.dictionary[symbol]
            replies.insert(0, word)
            self.model.update_context(symbol)
        return replies

    def babble(self, keys, words, used_key):
        symbol = 0
        node = None
        for i in xrange(0, self.model.order + 1):
            if self.model.context[i]:
                node = self.model.context[i]
        if not node or not node.tree:
            return 0, used_key
        branch = random.choice(node.tree)
        count = random.randrange(node.usage)
        while count >= 0:
            symbol = branch.symbol
            word = self.model.dictionary[symbol]
            if ((keys.find_word(word) != 0) and
                (used_key or self.aux.find_word(word) == 0) and
                (word not in words)):
                used_key = True
                break
            count -= branch.count
            if i >= len(node.tree) - 1:
                i = 0
            else:
                i += 1
        return symbol, used_key

    def seed(self, keys):
        if not self.model.context[0]:
            symbol = 0
        else:
            symbol = random.choice(self.model.context[0].tree).symbol

        if keys:
            i = random.randrange(len(keys))
            stop = i
            while True:
                word = keys[i]
                if ((self.model.dictionary.find_word(word) != 0) and
                    (self.aux.find_word(word) == 0)):
                    return self.model.dictionary.find_word(word)
                i += 1
                if i == len(keys):
                    i = 0
                if i == stop:
                    return symbol
        return symbol

    def make_keywords(self, words):
        keys = Dictionary()
        for word in words:
            c = 0
            for search, replace in self.swp:
                if search == word:
                    self.add_key(keys, replace)
                    c += 1
            if c == 0:
                self.add_key(keys, word)

        if keys:
            for word in words:
                c = 0
                for search, replace in self.swp:
                    if search == word:
                        self.add_aux(keys, replace)
                        c += 1
                if c == 0:
                    self.add_aux(keys, word)

        return keys

    def add_key(self, keys, word):
        if (self.model.dictionary.find_word(word) and
            word[0].isalnum() and
            not self.ban.find_word(word) and
            not self.aux.find_word(word)):
            keys.add_word(word)

    def add_aux(self, keys, word):
        if (self.model.dictionary.find_word(word) and
            word[0].isalnum() and
            not self.aux.find_word(word)):
            keys.add_word(word)

    # LEARNING FUNCTIONS

    def learn(self, words):
        if len(words) <= self.model.order:
            return
        self.model.initialize_context(self.model.forward)
        for word in words:
            symbol = self.model.dictionary.add_word(word)
            self.update_model(symbol)
        self.update_model(1)
        self.model.initialize_context(self.model.backward)
        for word in reversed(words):
            symbol = self.model.dictionary.find_word(word)
            self.update_model(symbol)
        self.update_model(1)

    def update_model(self, symbol):
        for i in xrange(self.model.order + 1, 0, -1):
            if self.model.context[i - 1]:
                node = self.model.context[i - 1].add_symbol(symbol)
                self.model.context[i] = node

    # UTILITY FUNCTIONS

    def make_words(self, input):
        offset = 0
        words = Dictionary()
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

    # DATA FILES

    @property
    def brain_file(self):
        return os.path.join(self.directory, 'halpy.brn')

    @property
    def train_file(self):
        return os.path.join(self.directory, 'halpy.trn')

    @property
    def ban_file(self):
        return os.path.join(self.directory, 'halpy.ban')

    @property
    def aux_file(self):
        return os.path.join(self.directory, 'halpy.aux')

    @property
    def swap_file(self):
        return os.path.join(self.directory, 'halpy.swp')


def main():
    """Parse args and create a simple chat bot"""
    parser = OptionParser(version=__version__)
    parser.add_option('-d', '--directory', metavar='<dir>', default=DIRECTORY,
                      help='base data directory (%default)')
    parser.add_option('-t', '--timeout', metavar='<seconds>', default=TIMEOUT,
                      type='float',
                      help='time to search for replies (%default)')
    parser.add_option('-o', '--order', metavar='<int>', default=ORDER,
                      type='int', help='size of contexts (%default)')
    hal = HAL(**parser.parse_args()[0].__dict__)
    try:
        while True:
            input = raw_input('>>> ').strip().lower()
            if not input:
                continue
            if input == '#quit':
                break
            if input == '#save':
                hal.save()
            else:
                print hal.process(input)
    except (EOFError, KeyboardInterrupt):
        print
    finally:
        t = time.time()
        hal.save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
