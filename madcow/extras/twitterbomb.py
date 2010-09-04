#!/usr/bin/env python

from optparse import OptionParser
import sys
import os
import logging as log
from include.utils import find_madcow

prefix, config = find_madcow()
sys.path.insert(0, prefix)

from madcow import DEFAULTS, Madcow
from include.config import Config
from periodic import tweetprinter

defaults = os.path.join(prefix, DEFAULTS)

ANNOYING = (# boing boing  D:
            'xenijardin',
            'doctorow',
            'BoingBoing',

            # generally irritating nonsense
            #'AKGovSarahPalin',  # yeah.. sarah palin... deleted?
            'kevinrose',        # some annoying internet star (digg founder)
            'meTakingAShit',    # descriptive shitter
            'TheMime',          # ...
            'macworld',         # lots of apple spam
            'tinybuddha',       # inane, shallow sayings
            'sfearthquakes',    # every 3.x quake in the geyser ever
            'PiMPY3WASH',       # some guys washing machine, seriously
            'cracked',          # cracked.com... kinda spammy and inane
            'DinDaaDaa',        # a markov bot
            'GusAndPenny',      # some guys catflap hooked up to twitter
            'FluffyTheCat',     # Meow...
            'Schwarzenegger',   # governator
            'Helen_Keller',     # grraaaaaarrrrhhh
            'sockington',       # jason scotts cat :(
            'big_ben_clock',    # BONG BONG BONG
            'big_ben_cock',     # DONG DONG DONG
            'newmoticons',      # random unicode shit
            'TW1TT3Rart',       # more random unicode shit
            'loadedsanta',      # lame

            # star TREK rp'ers
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
    optparse.add_option('-f', '--friend', metavar='NAME', help='add friend')
    opts, args = optparse.parse_args()

    log.root.setLevel(log.ERROR)
    api = tweetprinter.Main(Madcow(Config(config, defaults), prefix)).api
    friends = api.GetFriends()

    if opts.friend:
        print 'adding %s' % opts.friend
        api.CreateFriendship(opts.friend)

    if not opts.action:
        if opts.friend:
            return 0
        optparse.print_help()
        return 1


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
