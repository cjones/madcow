#!/usr/bin/env python

"""SQL model for HALpy"""

import sys
import warnings
warnings.simplefilter("ignore")
import MySQLdb

class SQLConnection(object):

    """Context manager that returns a cursor and commits when done"""

    def __init__(self, **dbinfo):
        self.connection = MySQLdb.connect(**dbinfo)

    def __enter__(self):
        return self.connection.cursor()

    def __exit__(self, *args):
        self.connection.commit()


class SQLBase(object):

    """Base class for SQL model"""

    sql = {}

    def __init__(self, table, connection):
        self.connection = connection
        for name, sql in self.sql.iteritems():
            setattr(self, name + '_sql', sql.replace('<TBL>', table))


class SQLTree(SQLBase):

    """Model of halpy markov chain tree"""

    sql = dict(get_word='SELECT id FROM <TBL> WHERE word = %s AND parent = %s',
               add_word='INSERT into <TBL> (word, parent) VALUES (%s, %s)',
               get_count='SELECT count FROM <TBL> WHERE id = %s',
               set_count='UPDATE <TBL> SET count = %s WHERE id = %s',
               get_usage='SELECT `usage` FROM <TBL> WHERE id = %s',
               set_usage='UPDATE <TBL> SET `usage` = %s WHERE id = %s')

    def add_word(self, node, word):
        with self.connection as cursor:
            found = self.find_word(node, word, add=True)
            self.set_count(found, self.get_count(found) + 1)
            self.set_usage(node, self.get_usage(node) + 1)
            return found

    def find_word(self, node, word, add=False):
        with self.connection as cursor:
            cursor.execute(self.get_word_sql, (word, node))
            found = cursor.fetchall()
            if found:
                return found[0][0]
            elif add:
                cursor.execute(self.add_word_sql, (word, node))
                cursor.execute(self.get_word_sql, (word, node))
                return cursor.fetchall()[0][0]

    def get_count(self, node):
        with self.connection as cursor:
            cursor.execute(self.get_count_sql, (node,))
            result = cursor.fetchone()
            if result:
                return result[0]

    def set_count(self, node, count):
        with self.connection as cursor:
            cursor.execute(self.set_count_sql, (count, node))

    def get_usage(self, node):
        with self.connection as cursor:
            cursor.execute(self.get_usage_sql, (node,))
            result = cursor.fetchone()
            if result:
                return result[0]

    def set_usage(self, node, usage):
        with self.connection as cursor:
            cursor.execute(self.set_usage_sql, (usage, node))


class SQLDictionary(SQLBase):

    """Model of halpy's dictionary of seen words"""

    sql = dict(get_word='SELECT id FROM <TBL> WHERE word = %s',
               add_word='INSERT INTO <TBL> (word) VALUES (%s)')

    def add_word(self, word):
        found = self.find_word(word)
        if found is None:
            with self.connection as cursor:
                cursor.execute(self.add_word_sql, (word,))
            found = self.find_word(word)
        return found

    def find_word(self, word):
        with self.connection as cursor:
            cursor.execute(self.get_word_sql, (word,))
            result = cursor.fetchone()
            if result:
                return result[0]


def main():
    connection = SQLConnection(user='tree', passwd='tree', db='tree')
    forward = SQLTree('forward', connection)
    backward = SQLTree('backward', connection)
    words = SQLDictionary('words', connection)
    return 0

if __name__ == '__main__':
    sys.exit(main())
