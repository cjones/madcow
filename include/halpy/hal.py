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

import sys
from optparse import OptionParser
import re
import random
import math
import time
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError
from sqlalchemy import (create_engine, Table, Column, Integer, VARCHAR,
                        MetaData, ForeignKey)

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__usage__ = '%prog [options] [training file, ...]'
__all__ = ['HAL']

# defaults
INTERACTIVE = True
URI = 'sqlite:///:memory:'
WORDS_TABLENAME = 'words'
FORWARD_TABLENAME = 'forward'
BACKWARD_TABLENAME = 'backward'
BAN_TABLENAME = 'ban_words'
AUX_TABLENAME = 'aux_words'
SWAP_TABLENAME = 'swap_words'
RESET = False
ORDER = 5

class Words(object):

    """Base table of words"""

    def __init__(self, string):
        self.string = string


class Tree(object):

    """Base table of markov model"""

    def __init__(self, word_id, parent_id):
        self.word_id = word_id
        self.used = 0
        self.count = 0
        self.parent_id = parent_id


class SwapList(object):

    """Table for word swap list"""

    def __init__(self, search, replace):
        self.search = search
        self.replace = replace


class Forward(Tree):

    """Markov model in forward direction"""


class Backward(Tree):

    """Markov model in backward direction"""


class BanList(Words):

    """List of words to ignore as keywords"""


class AuxList(Words):

    """List of auxiliary keywords"""


class HAL(object):

    """Heuristically programmed ALgorithmic Computer"""

    comment_re = re.compile(r'#.*$')
    boundary_re = re.compile(r"(\s+|[^a-z0-9']+)")
    endpunc = ('.', '!', '?')
    MAX_WORD_SIZE = 32
    TIMEOUT = 1

    def __init__(self, uri=URI, words_tablename=WORDS_TABLENAME,
                 forward_tablename=FORWARD_TABLENAME, order=ORDER,
                 backward_tablename=BACKWARD_TABLENAME, reset=RESET,
                 ban_tablename=BAN_TABLENAME, aux_tablename=AUX_TABLENAME,
                 swap_tablename=SWAP_TABLENAME):

        """Initialize HAL brain"""

        self.order = order

        # initialize object model
        engine = create_engine(uri)
        metadata = MetaData()
        Session = sessionmaker(bind=engine)

        words_table = Table(words_tablename, metadata,
                            Column('id', Integer, primary_key=True),
                            Column('string', VARCHAR(self.MAX_WORD_SIZE)))

        forward_table = Table(forward_tablename, metadata,
                              Column('id', Integer, primary_key=True),
                              Column('word_id', Integer,
                                     ForeignKey(words_tablename + '.id')),
                              Column('used', Integer),
                              Column('count', Integer),
                              Column('parent_id', Integer,
                                     ForeignKey(forward_tablename + '.id')))

        backward_table = Table(backward_tablename, metadata,
                               Column('id', Integer, primary_key=True),
                               Column('word_id', Integer,
                                      ForeignKey(words_tablename + '.id')),
                               Column('used', Integer),
                               Column('count', Integer),
                               Column('parent_id', Integer,
                                      ForeignKey(backward_tablename + '.id')))

        ban_table = Table(ban_tablename, metadata,
                          Column('id', Integer, primary_key=True),
                          Column('string', VARCHAR(self.MAX_WORD_SIZE)))

        aux_table = Table(aux_tablename, metadata,
                          Column('id', Integer, primary_key=True),
                          Column('string', VARCHAR(self.MAX_WORD_SIZE)))

        swap_table = Table(swap_tablename, metadata,
                           Column('id', Integer, primary_key=True),
                           Column('search', VARCHAR(self.MAX_WORD_SIZE)),
                           Column('replace', VARCHAR(self.MAX_WORD_SIZE)))

        mapper(Words, words_table)
        mapper(Forward, forward_table)
        mapper(Backward, backward_table)
        mapper(BanList, ban_table)
        mapper(AuxList, aux_table)
        mapper(SwapList, swap_table)

        self.session = Session()

        if reset:
            metadata.drop_all(engine)
            metadata.create_all(engine)
            error = Words('<ERROR>')
            self.session.add(error)
            self.session.commit()
            self.session.add(Words('<FIN>'))
            self.session.add(Forward(error.id, 0))
            self.session.add(Backward(error.id, 0))
            self.session.commit()

        self.forward = self.session.query(Forward).get(1)
        self.backward = self.session.query(Backward).get(1)

        # keep words preloaded to reduce sql queries
        self.words_id = {}
        self.words_string = {}
        for word in self.session.query(Words).all():
            self.words_string[word.string] = word.id
            self.words_id[word.id] = word.string

        # preload keyword constraints
        self.ban = [word.string for word in self.session.query(BanList).all()]
        self.aux = [word.string for word in self.session.query(AuxList).all()]
        self.swap = {}
        for word in self.session.query(SwapList).all():
            self.swap[word.search] = word.replace

    def train(self, path):
        """Train HAL from file (line sentence per line)"""
        for line in self.readlines(path):
            self.process(line, learn=True, reply=False)

    def process(self, line, learn=True, reply=True):
        """Process a line of input"""

        # normalize line and turn into list of words
        line = self.comment_re.sub('', line)
        line = line.strip()
        line = line.lower()
        strings = self.boundary_re.split(line)
        strings = [string.replace(' ', '<SPACE>')
                   for string in strings if string]
        if not strings:
            return
        if strings[-1][-1] not in self.endpunc:
            strings.append('.')

        if learn:
            self.learn(strings)
        if reply:
            return self.reply(strings)

    def interact(self):
        """Speak interactively to HAL until EOF/break"""
        try:
            while True:
                line = raw_input('>>> ')
                if line:
                    print hal.process(line)
        except (KeyboardInterrupt, EOFError):
            print

    # the rest of these functions are internal

    def learn(self, strings):
        if len(strings) <= self.order:
            return

        # update forward model
        self.init(self.forward)
        for string in strings:
            if string in self.words_string:
                id = self.words_string[string]
            else:
                # add new word and update cache
                word = Words(string)
                self.session.add(word)
                self.session.commit()
                id = word.id
                self.words_string[string] = id
                self.words_id[id] = string
            self.update(id, add=True)
        self.update(2, add=True)

        # update backward model
        self.init(self.backward)
        for string in reversed(strings):
            self.update(self.words_string[string], add=True)
        self.update(2, add=True)
        self.session.commit()

    def reply(self, strings):
        keys = []
        for string in strings:
            if string in self.swap:
                string = self.swap[string]
            if string not in self.words_string:
                continue
            if not string[0].isalnum():
                continue
            if string in self.ban:
                continue
            if string in self.aux:
                continue
            keys.append(string)

        if keys:
            for string in strings:
                if string in self.swap:
                    string = self.swap[string]
                if string not in self.words_string:
                    continue
                if not string[0].isalnum():
                    continue
                if string not in self.aux:
                    continue
                keys.append(string)

        max_surprise = -1.0
        basetime = time.time()
        output = None
        count = 0
        while time.time() - basetime < self.TIMEOUT:
            count += 1
            reply = []
            start = True
            self.init(self.forward)
            used_key = False

            while True:
                if start:
                    word_id = self.seed(keys)
                    start = False
                else:
                    word_id, used_key = self.babble(keys, reply, used_key)
                if word_id < 3:
                    break
                reply.append(self.words_id[word_id])
                self.update(word_id, add=False)

            self.init(self.backward)
            if reply:
                for i in xrange(min(len(reply) - 1, self.order), -1, -1):
                    self.update(self.words_string[reply[i]], add=False)

            while True:
                word_id, used_key = self.babble(keys, reply, used_key)
                if word_id < 3:
                    break
                reply.insert(0, self.words_id[word_id])
                self.update(word_id, add=False)

            surprise = self.evaluate_reply(keys, reply)
            if surprise > max_surprise:
                max_surprise = surprise
                output = reply

        if output:
            return ''.join(output).replace('<SPACE>', ' ').capitalize()
        else:
            return 'I am utterly speechless!'

    def seed(self, keys):
        if keys:
            i = random.randrange(len(keys))
            for string in keys[i:] + keys[:i]:
                if string in self.words_string and string not in self.aux:
                    return self.words_string[string]

        node = self.context[0]
        table = node.__class__
        query = self.session.query(table.word_id)
        query = query.filter_by(parent_id=node.id)
        tree = query.all()
        if tree:
            return random.choice(tree)[0]
        return 1

    def babble(self, keys, reply, used_key):
        word_id = 1
        for i in xrange(self.order + 1):
            if self.context[i] is not None:
                node = self.context[i]

        table = node.__class__
        query = self.session.query(table)
        query = query.filter_by(parent_id=node.id)
        tree = query.all()
        if not tree:
            return word_id, used_key

        i = random.randrange(len(tree))
        count = random.randrange(node.used)

        while count >= 0:
            child = tree[i]
            word_id = child.word_id
            string = self.words_id[word_id]

            if ((string in keys) and
                (used_key or (string not in self.aux)) and
                (string not in reply)):
                used_key = True
                break

            count -= child.count
            if i >= len(tree) - 1:
                i = 0
            else:
                i = i + 1

        return word_id, used_key

    def evaluate_reply(self, keys, reply):

        def calc_entropy(root, strings, n=0, entropy=0.0):
            table = root.__class__
            self.init(root)
            for string in strings:
                word_id = self.words_string[string]
                if string in keys:
                    prob = 0.0
                    count = 0;
                    n += 1
                    for i in xrange(self.order):
                        node = self.context[i]
                        if node:
                            query = self.session.query(table.count)
                            query = query.filter_by(parent_id = node.id,
                                                    word_id=word_id)
                            child = query.one()
                            child_count = child[0]
                            prob += float(child_count) / node.used
                            count += 1
                    if count:
                        entropy -= math.log(prob / count)
                self.update(word_id, add=False)
            return n, entropy

        n, entropy = calc_entropy(self.forward, reply)
        n, entropy = calc_entropy(self.backward, reversed(reply), n, entropy)
        if n >= 8:
            entropy /= math.sqrt(n - 1)
        if n >= 16:
            entropy /= n
        return entropy

    def init(self, node):
        self.context = [node] + [None] * (self.order + 1)

    def update(self, word_id, add=False):
        for i in xrange(self.order + 1, 0, -1):
            if self.context[i - 1]:
                node = self.context[i - 1]
                table = node.__class__
                try:
                    query = self.session.query(table)
                    query = query.filter_by(word_id=word_id, parent_id=node.id)
                    child = query.one()
                except NoResultFound:
                    if add:
                        child = table(word_id=word_id, parent_id=node.id)
                        self.session.add(child)
                        self.session.commit()
                    else:
                        child = self.session.query(table).get(1)
                self.context[i] = child
                if add:
                    child.count += 1
                    node.used += 1

    @classmethod
    def readlines(cls, path):
        with open(path, 'r') as file:
            for line in file:
                yield line


if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    parser = OptionParser(version=__version__, usage=__usage__)
    toggle = lambda bool: ('store_%s' % (not bool)).lower()
    parser.add_option('-i', dest='interactive', default=INTERACTIVE,
                      action=toggle(INTERACTIVE),
                      help='run interactively (default: %default)')
    parser.add_option('-u', dest='uri', metavar='<uri>', default=URI,
                      help='database URI (default: %default)')
    parser.add_option('-r', dest='reset', default=RESET, action=toggle(RESET),
                      help='reset database (default: %default)')
    parser.add_option('-o', dest='order', metavar='<int>', default=ORDER,
                      type='int', help='markov order (default: %default)')
    opts, args = parser.parse_args()
    interactive = opts.interactive
    del opts.interactive

    try:
        hal = HAL(**opts.__dict__)
        for file in args:
            hal.train(file)
        if interactive:
            hal.interact()
    except OperationalError, error:
        if 'no such table' in str(error):
            parser.error('missing tables, try running with -r')
        raise error
    sys.exit(0)
