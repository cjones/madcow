#!/usr/bin/env python

import sys
import warnings
warnings.simplefilter("ignore")
import MySQLdb

class Tree(object):

    def __init__(self, **kwargs):
        self.connection = MySQLdb.connect(**kwargs)

    def reset(self):
        cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()


def main():
    connection = dict(user='tree', passwd='tree', db='tree')
    forward = Tree('forward', **connection)
    forward.reset()
    backward = Tree('backward', **connection)
    backward.reset()
    return 0

if __name__ == '__main__':
    sys.exit(main())
