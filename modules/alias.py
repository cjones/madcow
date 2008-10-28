#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Manage aliases"""

from __future__ import with_statement
from include.utils import Module
import logging as log
import re
import os

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = ['Main']

class AliasError(Exception):

    """Raised when there's an error with alias db"""


class Alias(object):

    """Represents a single alias"""

    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.pattern = re.compile(r'\b%s\b' % re.escape(key), re.I)


class AliasDB(object):

    """Interface to alias flat file database"""

    def __init__(self, path):
        self.path = path
        self.aliases = []
        if not os.path.exists(path):
            with open(path, 'wb') as file:
                pass
        with open(path, 'rb') as file:
            for line in file:
                try:
                    key, val = line.strip().split(None, 1)
                    self.aliases.append(Alias(key, val))
                except Exception, error:
                    raise AliasError('problem parsing db: %s' % error)

    def save(self):
        with open(self.path, 'wb') as file:
            for alias in self:
                print >> file, '%s %s' % (alias.key, alias.val)

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
    require_addressing = False
    help = 'alias [ add <key> <val> | del <#> | list ] - manage aliases'
    priority = 0
    terminate = False
    allow_threading = False
    command_re = re.compile(r'^\s*alias\s+(add|list|del)\s*?(?:\s+(.+?)\s*)?$',
                            re.I)

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.db = AliasDB(os.path.join(madcow.prefix, 'data',
                                       'db-%s-alias' % madcow.namespace))

    def response(self, nick, args, kwargs):
        try:
            line = args[0]
            try:
                command, args = self.command_re.search(line).groups()
                kwargs['req'].matched = True
                return self.runcommand(command, args)
            except AliasError, error:
                return '%s: %s' % (nick, error)
            except AttributeError:
                self.checkalias(line, kwargs)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return '%s: %s' % (nick, error)

    def runcommand(self, command, args):
        """User invoked alias command"""
        if args is None:
            args = ''
        command = command.lower()
        args = args.split(None, 1)
        if command == 'add':
            if len(args) != 2:
                raise AliasError(self.help)
            for name, obj in self.madcow.modules.by_priority():
                if obj.pattern is Module._any:
                    continue
                if obj.pattern.search(args[0]):
                    raise AliasError('that pattern would override %s' % name)
            for alias in self.db:
                if alias.key == args[0]:
                    raise AliasError('that alias already exists')
            self.db.add(*args)
            return 'alias added'
        elif command == 'list':
            if len(args):
                raise AliasError(self.help)
            output = []
            for i, alias in enumerate(self.db):
                output.append('[%d] %s => %s' % (i + 1, alias.key, alias.val))
            if output:
                return '\n'.join(output)
            return 'no aliases defined'
        elif command == 'del':
            if len(args) != 1:
                raise AliasError(self.help)
            index = args[0]
            if not index.isdigit():
                raise AliasError('alias must be a #')
            index = int(index)
            if not len(self.db):
                raise AliasError('no aliases to remove')
            if index < 1 or index > len(self.db):
                raise AliasError('invalid alias key')
            index -= 1
            key = self.db[index].key
            self.db.delete(index)
            return 'deleted alias: %s' % key

    def checkalias(self, line, kwargs):
        """Check for alias substitution"""
        for alias in self.db:
            new = alias.pattern.sub(alias.val, line, 1)
            if new != line:
                kwargs['req'].message = new
                break

