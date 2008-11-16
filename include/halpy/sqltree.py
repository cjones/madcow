#!/usr/bin/env python

import sys
import warnings
warnings.simplefilter("ignore")
import MySQLdb

class SQLConnection(object):

    def __init__(self, **dbinfo):
        self.connection = MySQLdb.connect(**dbinfo)

    def __enter__(self):
        return self.connection.cursor()

    def __exit__(self, *args):
        self.connection.commit()


class SQLBase(object):

    def __init__(self, table, connection):
        self.table = table
        self.connection = connection


class SQLTree(SQLBase):

    pass


class SQLDictionary(SQLBase):

    pass


def main():
    connection = SQLConnection(user='tree', passwd='tree', db='tree')
    forward = SQLTree('forward', connection)
    backward = SQLTree('backward', connection)
    words = SQLDictionary('words', connection)
    return 0

if __name__ == '__main__':
    sys.exit(main())
