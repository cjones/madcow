#!/usr/bin/env python

import sys
import warnings
warnings.simplefilter("ignore")
import MySQLdb

class Tree(object):

    create_sql = ["DROP TABLE IF EXISTS `%(table)s`;",
                  ("CREATE TABLE `%(table)s` ("
                   "    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,"
                   "    `symbol` int(10) unsigned NOT NULL,"
                   "    `usage` int(10) unsigned NOT NULL DEFAULT '0',"
                   "    `count` int(10) unsigned NOT NULL DEFAULT '0',"
                   "    `parent` int(10) unsigned DEFAULT NULL,"
                   "    PRIMARY KEY (`id`),"
                   "    UNIQUE KEY `no_dupe_symbols` (`symbol`,`parent`),"
                   "    KEY `tree` (`id`,`parent`)"
                   ") ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;"),
                  "LOCK TABLES `%(table)s` WRITE;",
                  "INSERT INTO `%(table)s` VALUES (1,0,0,0,NULL);",
                  "UNLOCK TABLES;"]

    def __init__(self, table, **kwargs):
        self.table = table
        self.connection = MySQLdb.connect(**kwargs)

    def reset(self):
        cursor = self.connection.cursor()
        for sql in self.create_sql:
            cursor.execute(sql % {'table': self.table})
        self.connection.commit()

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
