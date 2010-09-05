#!/usr/bin/env python

"""Manage aliases"""

import re
import os
from madcow.util import Module

class AliasError(Exception):

    """Raised when there's an error with alias db"""


class Alias(object):

    """Represents a single alias"""

    def __init__(self, key, val):
        self.key = key
        self.val = val
        # \b doesn't work with unicode chars
        self.pattern = re.compile(ur'^\s*' + re.escape(key) + ur'(:|\s+|$)', re.I)


class AliasDB(object):

    """Interface to alias flat file database"""

    def __init__(self, path, charset='ascii'):
        self.path = path
        self.charset = charset
        self.aliases = []
        if not os.path.exists(path):
            with open(path, 'wb') as file:
                pass
        with open(path, 'rb') as file:
            for line in file:
                try:
                    key, val = line.strip().split(None, 1)
                    key = key.decode(self.charset, 'replace')
                    val = val.decode(self.charset, 'replace')
                    self.aliases.append(Alias(key, val))
                except Exception, error:
                    raise AliasError(u'problem parsing db: %s' % error)

    def save(self):
        with open(self.path, 'wb') as file:
            for alias in self:
                key = alias.key.encode(self.charset, 'replace')
                val = alias.val.encode(self.charset, 'replace')
                print >> file, '%s %s' % (key, val)

    def delete(self, index):
        self.aliases.pop(index)
        self.save()

    def add(self, key, val):
        self.aliases.append(Alias(key, val))
        self.save()

    def __getslice__(self, start, end):
        return self.aliases[start:end]

    def __getitem__(self, item):
        return self.aliases[item]

    def __len__(self):
        return len(self.aliases)

    def __iter__(self):
        for alias in self.aliases:
            yield alias


class Main(Module):

    pattern = Module._any
    require_addressing = True
    help = u'alias [ add <key> <val> | del <#> | list ] - manage aliases'
    priority = 0
    terminate = False
    allow_threading = False
    command_re = re.compile(r'^\s*alias\s+(add|list|del)\s*?(?:\s+(.+?)\s*)?$', re.I)

    def init(self):
        self.db = AliasDB(os.path.join(self.madcow.base, 'db', 'alias'), charset=self.madcow.charset)

    def response(self, nick, args, kwargs):
        line = args[0]
        try:
            command, args = self.command_re.search(line).groups()
            kwargs[u'req'].matched = True
            return self.runcommand(command, args)
        except AliasError, error:
            return u'%s: %s' % (nick, error)
        except AttributeError:
            self.checkalias(line, kwargs)

    def runcommand(self, command, args):
        """User invoked alias command"""
        if args is None:
            args = u''
        command = command.lower()
        args = args.split(None, 1)
        if command == u'add':
            if len(args) != 2:
                raise AliasError(self.help)
            for name, mod in self.madcow.modules.by_priority():
                obj = mod['obj']
                if obj.pattern is Module._any:
                    continue
                if obj.pattern.search(args[0]):
                    raise AliasError(u'that pattern would override %s' % name)
            for alias in self.db:
                if alias.key == args[0]:
                    raise AliasError(u'that alias already exists')
            self.db.add(*args)
            return u'alias added'
        elif command == u'list':
            if len(args):
                raise AliasError(self.help)
            output = []
            for i, alias in enumerate(self.db):
                output.append(u'[%d] %s => %s' % (i + 1, alias.key, alias.val))
            if output:
                return u'\n'.join(output)
            return u'no aliases defined'
        elif command == u'del':
            if len(args) != 1:
                raise AliasError(self.help)
            index = args[0]
            if not index.isdigit():
                raise AliasError(u'alias must be a #')
            index = int(index)
            if not len(self.db):
                raise AliasError(u'no aliases to remove')
            if index < 1 or index > len(self.db):
                raise AliasError(u'invalid alias key')
            index -= 1
            key = self.db[index].key
            self.db.delete(index)
            return u'deleted alias: %s' % key

    def checkalias(self, line, kwargs):
        """Check for alias substitution"""
        for alias in self.db:
            new = alias.pattern.sub(alias.val + r'\1', line, 1)
            if new != line:
                kwargs[u'req'].message = new
                break
