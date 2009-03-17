#!/usr/bin/env python

from optparse import OptionParser
import sys
import os
import logging as log

def find_madcow():
    """Find where we are run from and config file location"""
    prefix = sys.argv[0] if __file__.startswith(sys.argv[0]) else __file__
    prefix = os.path.dirname(prefix)
    prefix = os.path.abspath(prefix)
    parts = prefix.split(os.sep)
    while parts:
        prefix = os.sep.join(parts)
        config = os.path.join(prefix, 'madcow.ini')
        if os.path.exists(config):
            break
        parts.pop()
    return prefix, config

PREFIX, CONFIG = find_madcow()
sys.path.insert(0, PREFIX)

from madcow import Config, Madcow
from periodic import tweetprinter

ANNOYING = (# boing boing
            'xenijardin',
            'doctorow',
            'BoingBoing',

            # generally irritating nonsense
            'kevinrose',
            #'TheMime',  # I LIKE THE MIME
            'macworld',
            'tinybuddha',
            'sfearthquakes',
            'PiMPY3WASH',
            'cracked',

            # star wars rp'ers
            'JeanLuc_Picard',
            'LtWorf',
            'wesley_crusher',
            '_Data',
            'Will_Riker',
            'DeannaTroi',
            'Geordi_La_Forge',
            'BeverlyHCrusher',
            'Chief_OBrien',
            'LwaxanaTroi')

def main():
    # dest metavar default action type nargs const choices callback help
    # store[_(const|true|false) append[_const] count callback
    # string int long float complex choice
    optparse = OptionParser()
    optparse.add_option('-a', '--add-annoying', dest='action',
                        default=None, action='store_const', const='add',
                        help='add annoying people')
    optparse.add_option('-d', '--del-annoying', dest='action',
                        action='store_const', const='del',
                        help='delete annoying people')
    optparse.add_option('-l', '--list', dest='action', action='store_const',
                        const='list', help='list friends')
    opts, args = optparse.parse_args()

    if not opts.action:
        optparse.print_help()
        return 1

    log.root.setLevel(log.ERROR)
    api = tweetprinter.Main(Madcow(Config(CONFIG), PREFIX)).api
    friends = api.GetFriends()

    if opts.action == 'list':
        for friend in friends:
            print friend.GetScreenName()

    elif opts.action == 'del':
        for friend in friends:
            name = friend.GetScreenName()
            if name in ANNOYING:
                print 'removing: %s' % name
                api.DestroyFriendship(name)

    elif opts.action == 'add':
        names = [friend.GetScreenName() for friend in friends]
        for name in ANNOYING:
            if name not in names:
                print 'adding: %s' % name
                api.CreateFriendship(name)

    return 0

if __name__ == '__main__':
    sys.exit(main())
