#!/usr/bin/env python

"""Reference model, straight port of the C version"""

from __future__ import with_statement
import sys
import os
import re
from random import randrange as rnd
import time
import math
from optparse import OptionParser
import cPickle as pickle

class Base(object):

    comment_re = re.compile(r'#.*$')

    def __repr__(self):
        attrs = ('%s=%s' % (k, repr(v)) for k, v in self.__dict__.iteritems())
        return '<%s: %s>' % (self.__class__.__name__, ', '.join(attrs))

    @classmethod
    def wordcmp(cls, word1, word2):
        bound = min(word1.length, word2.length)
        for i in cls.crange(0, '<', bound, +1):
            if word1.word[i].upper() != word2.word[i].upper():
                return ord(word1.word[i].upper()) - ord(word2.word[i].upper())
        if word1.length < word2.length:
            return -1
        if word1.length > word2.length:
            return 1
        return 0

    @staticmethod
    def crange(start, test='<', stop=None, step=1):
        """C-like forloop syntax to make porting easier"""
        if stop is None:
            start, stop = 0, start
        if step > 0 and test == '<=':
            stop += 1
        elif step < 0 and test == '>=':
            stop -= 1
        return xrange(start, stop, step)


class Swap(Base):

    def __init__(self, filename):
        self.size = 0
        self.sfrom = Array(String)
        self.sto = Array(String)
        if not os.path.exists(filename):
            return
        with open(filename, 'r') as file:
            for line in file:
                line = self.comment_re.sub('', line)
                line = line.strip()
                try:
                    sfrom, sto = line.split(None, 1)
                except ValueError:
                    continue
                self.add_swap(sfrom, sto)

    def add_swap(self, s, d):
        self.size += 1
        self.sfrom[self.size - 1].length = len(s)
        self.sfrom[self.size - 1].word = s
        self.sto[self.size - 1].length = len(d)
        self.sto[self.size - 1].word = d


class Array(list):

    """List that automagically grows on unallocated assignment"""

    def __init__(self, default=None):
        self.default = default
        self.type = isinstance(default, type)
        super(Array, self).__init__()

    def __getitem__(self, key):
        self.grow(key)
        return super(Array, self).__getitem__(key)

    def __setitem__(self, key, val):
        self.grow(key)
        super(Array, self).__setitem__(key, val)

    def grow(self, key):
        size = key + 1 - len(self)
        for i in range(size):
            self.append(self.default() if self.type else self.default)

    def __str__(self):
        return ''.join(self)

    def __repr__(self):
        return '<Array: %s>' % list.__repr__(self)


class Dictionary(Base):

    def __init__(self):
        self.size = 0
        self.index = Array(int)
        self.entry = Array(String)

    def add_word(self, word):
        position, found = self.search(word)
        if not found:
            self.size += 1
            self.entry[self.size - 1].length = word.length
            self.entry[self.size - 1].word = ''
            for i in self.crange(0, '<', word.length, +1):
                self.entry[self.size - 1].word += word.word[i]
            for i in self.crange(self.size - 1, '>', position, -1):
                self.index[i] = self.index[i - 1]
            self.index[position] = self.size - 1
        return self.index[position]

    def search(self, word):
        if self.size == 0:
            return 0, False
        min = 0
        max = self.size - 1
        while True:
            middle = (min + max) / 2
            compar = self.wordcmp(word, self.entry[self.index[middle]])
            if compar == 0:
                return middle, True
            elif compar > 0:
                if max == middle:
                    return middle + 1, False
                min = middle + 1
            else:
                if min == middle:
                    return middle, False
                max = middle - 1

    def find_word(self, word):
        position, found = self.search(word)
        if found:
            return self.index[position]
        return 0

    def word_exists(self, word):
        for i in self.crange(0, '<', self.size, +1):
            if self.wordcmp(self.entry[i], word) == 0:
                return True
        return False

    def __iter__(self):
        for i in self.entry:
            yield i.word


class List(Dictionary):

    def __init__(self, filename):
        super(List, self).__init__()
        if not os.path.exists(filename):
            return
        with open(filename, 'r') as file:
            for line in file:
                line = self.comment_re.sub('', line)
                line = line.strip()
                for word in line.split():
                    if word:
                        self.add_word(String(len(word), word))


class Tree(Base):

    def __init__(self):
        self.symbol = 0
        self.usage = 0
        self.count = 0
        self.branch = 0
        self.tree = Array(Tree)

    def add_symbol(self, symbol):
        node = self.find_symbol_add(symbol)
        if node.count < 65535:
            node.count += 1
            self.usage += 1
        return node

    def find_symbol_add(self, symbol):
        i, found_symbol = self.search_node(symbol)
        if found_symbol:
            found = self.tree[i]
        else:
            found = Tree()
            found.symbol = symbol
            self.add_node(found, i)
        return found

    def find_symbol(self, symbol):
        i, found_symbol = self.search_node(symbol)
        if found_symbol:
            return self.tree[i]

    def add_node(self, node, position):
        for i in self.crange(self.branch, '>', position, -1):
            self.tree[i] = self.tree[i - 1]
        self.tree[position] = node
        self.branch += 1

    def search_node(self, symbol):
        if self.branch == 0:
            return 0, False
        min = 0
        max = self.branch - 1
        while True:
            middle = int((min + max) / 2)
            compar = symbol - self.tree[middle].symbol
            if compar == 0:
                return middle, True
            elif compar > 0:
                if max == middle:
                    return middle + 1, False
                min = middle + 1
            else:
                if min == middle:
                    return middle, False
                max = middle - 1


class String(Base):

    def __init__(self, length=None, word=None):
        self.length = length
        self.word = word

    def __str__(self):
        return self.word


class Model(Base):

    def __init__(self, order):
        self.order = order
        self.forward = Tree()
        self.backward = Tree()
        self.context = Array(Tree)
        self.initialize_context()
        self.dictionary = Dictionary()
        self.dictionary.add_word(String(7, '<ERROR>'))
        self.dictionary.add_word(String(5, '<FIN>'))

    def initialize_context(self):
        for i in self.crange(0, '<=', self.order, +1):
            self.context[i] = None

    def update_context(self, symbol):
        for i in self.crange(self.order + 1, '>', 0, -1):
            if self.context[i - 1] is not None:
                self.context[i] = self.context[i - 1].find_symbol(symbol)


class HAL(Base):

    DEFAULT = '.'
    ORDER = 5
    TIMEOUT = 1

    punc_re = re.compile(r'[!.?]')

    def __init__(self, directory=None):
        self.directory = directory
        self.last = None
        self.words = Dictionary()
        self.greets = Dictionary()
        self.change_personality()

    def change_personality(self, new=None):
        if not self.directory:
            self.directory = self.DEFAULT
        if not self.last:
            self.last = self.directory
        if new:
            self.directory = new
        self.load_personality()

    def load_personality(self):
        self.model = Model(self.ORDER)
        filename = os.path.join(self.directory, 'megahal.brn')
        if os.path.exists(filename):
            with open(filename, 'rb') as file:
                self.model = pickle.load(file)
        else:
            filename = os.path.join(self.directory, 'megahal.trn')
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    for line in file:
                        self.teach(line.strip())
        self.ban = List(os.path.join(self.directory, 'megahal.ban'))
        self.aux = List(os.path.join(self.directory, 'megahal.aux'))
        self.grt = List(os.path.join(self.directory, 'megahal.grt'))
        self.swp = Swap(os.path.join(self.directory, 'megahal.swp'))

    def process(self, input):
        input = input.upper()
        words = self.make_words(input)
        self.learn(words)
        output = self.generate_reply(words)
        return output.capitalize()

    def teach(self, input):
        input = input.upper()
        words = self.make_words(input)
        self.learn(words)

    def save(self):
        self.model.initialize_context()
        filename = os.path.join(self.directory, 'megahal.brn')
        with open(filename, 'wb') as file:
            pickle.dump(self.model, file)

    def generate_reply(self, words):
        timeout = self.TIMEOUT
        output = ''
        keywords = self.make_keywords(words)
        dummy = Dictionary()
        replywords = self.reply(dummy)
        if self.dissimilar(words, replywords):
            output = self.make_output(replywords)

        max_surprise = -1.0
        count = 0
        basetime = time.time()
        output = self.make_output(replywords)
        while time.time() - basetime < timeout:
            replywords = self.reply(keywords)
            surprise = self.evaluate_reply(keywords, replywords)
            count += 1
            if ((surprise > max_surprise) and
                (self.dissimilar(words, replywords) is True)):
                max_surprise = surprise
                output = self.make_output(replywords)
        return output

    def evaluate_reply(self, keys, words):
        entropy = 0.0
        num = 0
        if words.size <= 0:
            return entropy
        self.model.initialize_context()
        self.model.context[0] = self.model.forward
        for i in self.crange(0, '<', words.size, +1):
            symbol = self.model.dictionary.find_word(words.entry[i])
            if keys.find_word(words.entry[i]) != 0:
                probability = 0.0
                count = 0
                num += 1
                for j in self.crange(0, '<', self.model.order, +1):
                    if self.model.context[j] is not None:
                        node = self.model.context[j].find_symbol(symbol)
                        probability += (float(node.count) /
                                        self.model.context[j].usage)
                        count += 1
                if count > 0.0:
                    entropy -= math.log(probability / count)
            self.model.update_context(symbol)

        self.model.initialize_context()
        self.model.context[0] = self.model.backward
        for k in self.crange(words.size - 1, '>=', 0, -1):
            symbol = self.model.dictionary.find_word(words.entry[k])
            if keys.find_word(words.entry[k]) != 0:
                probability = 0.0
                count = 0
                num += 1
                for j in self.crange(0, '<', self.model.order, +1):
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

    def make_output(self, words):
        output = ''
        if words.size == 0:
            return 'I am utterly speechless!'
        return ''.join(words)

    def reply(self, keys):
        start = True
        replies = Dictionary()
        self.model.initialize_context()
        self.model.context[0] = self.model.forward
        used_key = False
        while True:
            if start:
                symbol = self.seed(keys)
            else:
                symbol, used_key = self.babble(keys, replies, used_key)
            if symbol == 0 or symbol == 1:
                break
            start = False
            reply = self.model.dictionary.entry[symbol]
            replies.entry[replies.size].length = reply.length
            replies.entry[replies.size].word = reply.word
            replies.size += 1
            self.model.update_context(symbol)

        self.model.initialize_context()
        self.model.context[0] = self.model.backward
        if replies.size > 0:
            val = min(replies.size - 1, self.model.order)
            for i in self.crange(val, '>=', 0, -1):
                symbol = self.model.dictionary.find_word(replies.entry[i])
                self.model.update_context(symbol)

        while True:
            symbol, used_key = self.babble(keys, replies, used_key)
            if symbol == 0 or symbol == 1:
                break
            for i in self.crange(replies.size, '>', 0, -1):
                replies.entry[i].length = replies.entry[i - 1].length
                replies.entry[i].word = replies.entry[i - 1].word

            word = self.model.dictionary.entry[symbol]
            replies.entry[0].length = word.length
            replies.entry[0].word = word.word
            replies.size += 1
            self.model.update_context(symbol)

        return replies

    def babble(self, keys, words, used_key):
        symbol = 0
        node = None
        for i in self.crange(0, '<=', self.model.order, +1):
            if self.model.context[i]:
                node = self.model.context[i]
        if not node or node.branch == 0:
            return 0, used_key
        i = rnd(node.branch)
        count = rnd(node.usage)
        while count >= 0:
            symbol = node.tree[i].symbol
            if ((keys.find_word(self.model.dictionary.entry[symbol]) != 0) and
                ((used_key) or
                 (self.aux.find_word(self.model.dictionary.entry[symbol]) == 0))
                and
                (not words.word_exists(self.model.dictionary.entry[symbol]))):
                used_key = True
                break
            count -= node.tree[i].count
            if i >= node.branch -1:
                i = 0
            else:
                i += 1
        return symbol, used_key

    def seed(self, keys):
        if self.model.context[0].branch == 0:
            symbol = 0
        else:
            val = rnd(self.model.context[0].branch)
            symbol = self.model.context[0].tree[val].symbol

        if keys.size > 0:
            i = rnd(keys.size)
            stop = i
            while True:
                word = keys.entry[i]
                if ((self.model.dictionary.find_word(word) != 0) and
                    (self.aux.find_word(word) == 0)):
                    return self.model.dictionary.find_word(word)
                i += 1
                if i == keys.size:
                    i = 0
                if i == stop:
                    return symbol
        return symbol

    def make_keywords(self, words):
        keys = Dictionary()
        for i in self.crange(0, '<', words.size, +1):
            c = 0
            for j in self.crange(0, '<', self.swp.size, +1):
                if self.wordcmp(self.swp.sfrom[j], words.entry[i]) == 0:
                    self.add_key(keys, self.swp.sto[j])
                    c += 1
            if c == 0:
                self.add_key(keys, words.entry[i])

        if keys.size > 0:
            for i in self.crange(0, '<', words.size, +1):
                c = 0
                for j in self.crange(0, '<', self.swp.size, +1):
                    if self.wordcmp(self.swp.sfrom[j], words.entry[i]) == 0:
                        self.add_aux(keys, self.swp.sto[j])
                        c += 1
                if c == 0:
                    self.add_aux(keys, words.entry[i])

        return keys

    def add_key(self, keys, word):
        if (self.model.dictionary.find_word(word) and
            word.word[0].isalnum() and
            not self.ban.find_word(word) and
            not self.aux.find_word(word)):
            keys.add_word(word)

    def add_aux(self, keys, word):
        if (self.model.dictionary.find_word(word) and
            word.word[0].isalnum() and
            not self.aux.find_word(word)):
            keys.add_word(word)

    def learn(self, words):
        if words.size <= self.model.order:
            return
        self.model.initialize_context()
        self.model.context[0] = self.model.forward
        for i in self.crange(0, '<', words.size, +1):
            symbol = self.model.dictionary.add_word(words.entry[i])
            self.update_model(symbol)
        self.update_model(1)
        self.model.initialize_context()
        self.model.context[0] = self.model.backward
        for i in self.crange(words.size - 1, '>=', 0, -1):
            symbol = self.model.dictionary.find_word(words.entry[i])
            self.update_model(symbol)
        self.update_model(1)

    def update_model(self, symbol):
        for i in self.crange(self.model.order + 1, '>', 0, -1):
            if self.model.context[i - 1]:
                node = self.model.context[i - 1].add_symbol(symbol)
                self.model.context[i] = node

    def make_words(self, input):
        offset = 0
        words = Dictionary()
        if not input:
            return words
        while True:
            if self.boundary(input, offset):
                words.entry[words.size].length = offset
                words.entry[words.size].word = input
                words.size += 1
                if offset == len(input):
                    break
                input = input[offset:]
                offset = 0
            else:
                offset += 1
        last = words.entry[words.size - 1]
        if last.word[0].isalnum():
            words.entry[words.size].length = 1
            words.entry[words.size].word = '.'
            words.size += 1
        elif not self.punc_re.search(last.word[last.length - 1]):
            last.length = 1
            last.word = '.'
        return words

    @classmethod
    def dissimilar(cls, words1, words2):
        if words1.size != words2.size:
            return True
        for i in cls.crange(0, '<', words1.size, +1):
            if cls.wordcmp(words1.entry[i], words2.entry[i]) != 0:
                return True
        return False

    @staticmethod
    def boundary(string, position):
        if position == 0:
            return False
        if position == len(string):
            return True
        if ((string[position] == "'") and
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
    parser = OptionParser()
    parser.add_option('-d', '--directory', metavar='<dir>')
    opts = parser.parse_args()[0]
    hal = HAL(directory=opts.directory)
    try:
        while True:
            input = raw_input('>>> ').strip()
            if input == 'quit':
                break
            elif input:
                print hal.process(input)
    except (EOFError, KeyboardInterrupt):
        print
    finally:
        hal.save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
