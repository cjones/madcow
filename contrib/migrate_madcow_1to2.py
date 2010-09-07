#!/usr/bin/env python

"""Migrate a madcow installation from 1.x to 2.x"""

import sys
from optparse import OptionParser
import shelve
import os
import shutil
from ConfigParser import ConfigParser, NoOptionError
from madcow.conf import defaults as settings
import madcow
import tty
from select import select, error as SelectError
import errno
from datetime import datetime

try:
    import dbm
except ImportError:
    import anydbm as dbm

__version__ = '0.1'

BRAIN_FILES = ['megahal.aux', 'megahal.ban', 'megahal.dic', 'megahal.brn', 'megahal.swp', 'megahal.trn']
RENAMED_MODULES = {'terror': 'war', 'election': 'election2008', 'translate': 'babel'}

def copy(src, dst):
    shutil.copy(src, dst)
    print 'copied %s' % os.path.basename(dst)


def getkey(timeout=None):
    fd = sys.stdin.fileno()
    attr = tty.tcgetattr(fd)
    tty.setraw(fd)
    try:
        while True:
            try:
                if fd in select([fd], [], [], timeout)[0]:
                    return os.read(fd, 1)
            except (OSError, IOError, SelectError), error:
                if error.args[0] != errno.EINTR:
                    raise
    finally:
        tty.tcsetattr(fd, tty.TCSADRAIN, attr)


def write(data):
    sys.stdout.write(data)
    sys.stdout.flush()


def validate_list(name, objects):
    objects = list(set(objects))
    print 'Found multiple %s: %s' % (name, ', '.join(objects))
    new = []
    for object in objects:
        write('%s - keep (y/n)? ' % object)
        keep = None
        while True:
            key = getkey()
            if not key:
                break
            key = key.lower()
            if key == 'y':
                print 'Yes'
                keep = True
                break
            elif key == 'n':
                print 'No'
                keep = False
                break
            elif key == '\x03':
                raise KeyboardInterrupt
        if keep:
            new.append(object)
    return new


def migrate(fromdir, todir):
    os.makedirs(todir)
    dbdir = os.path.join(todir, 'db')
    if not os.path.exists(dbdir):
        os.makedirs(dbdir)
    data = None
    config = ConfigParser()
    config.read(os.path.join(fromdir, 'include', 'defaults.ini'))
    for filename in os.listdir(fromdir):
        src = os.path.join(fromdir, filename)
        if filename == 'grufti-responses.txt':
            copy(src, os.path.join(todir, 'response.grufti'))
        elif filename == 'data':
            data = src
        elif filename == 'madcow.ini':
            config.read(src)

    # migrate settings
    nicks = set()
    nicks.add(config.get('irc', 'nick'))
    nicks.add(config.get('silcplugin', 'nick'))
    settings.PROTOCOL = config.get('main', 'module')
    settings.IRC_HOST = config.get('irc', 'host')
    settings.IRC_PORT = config.getint('irc', 'port')
    settings.IRC_SSL = config.get('irc', 'ssl') == 'yes'
    settings.IRC_PASSWORD = config.get('irc', 'password')
    settings.IRC_RECONNECT = config.get('irc', 'reconnect') == 'yes'
    settings.IRC_RECONNECT_WAIT = config.getint('irc', 'reconnectWait')
    settings.IRC_REJOIN = config.get('irc', 'rejoin') == 'yes'
    settings.IRC_REJOIN_WAIT = config.getint('irc', 'rejoinWait')
    settings.IRC_REJOIN_MESSAGE = config.get('irc', 'rejoinReply')
    settings.IRC_QUIT_MESSAGE = config.get('irc', 'quitMessage')
    settings.IRC_OPER = config.get('irc', 'oper') == 'yes'
    settings.IRC_OPER_PASS = config.get('irc', 'operPass')
    settings.IRC_OPER_USER = config.get('irc', 'operUser')
    settings.IRC_NICKSERV_PASS = config.get('irc', 'nickServPass')
    settings.IRC_NICKSERV_USER = config.get('irc', 'nickServUser')
    settings.IRC_FORCE_WRAP = config.getint('irc', 'wrapSize')
    settings.IRC_DELAY_LINES = config.getint('irc', 'delay')
    settings.IRC_IDENTIFY_NICKSERV = bool(settings.IRC_NICKSERV_PASS and settings.IRC_NICKSERV_USER)
    settings.IRC_KEEPALIVE = config.get('irc', 'keepalive') == 'yes'
    settings.IRC_KEEPALIVE_FREQ = config.getint('irc', 'keepalive_freq')
    settings.IRC_KEEPALIVE_TIMEOUT = config.getint('irc', 'keepalive_timeout')
    settings.IRC_RECONNECT_MESSAGE = settings.IRC_REJOIN_MESSAGE
    settings.MODULES = []
    for module in os.listdir(os.path.join(madcow.PREFIX, 'modules')):
        if module.endswith('.py') and module != '__init__.py':
            module = module.replace('.py', '')
            try:
                try:
                    test = RENAMED_MODULES[module]
                except KeyError:
                    test = module
                if config.get('modules', test) == 'yes':
                    settings.MODULES.append(module)
                else:
                    print >> sys.stderr, 'WARN: %r module is disabled' % module
            except NoOptionError:
                print >> sys.stderr, 'WARN: unknown module: %r' % module
    if config.get('steam', 'enabled') == 'yes':
        settings.MODULES.append('steam')
    settings.STEAM_GROUP = config.get('steam', 'group')
    settings.STEAM_SHOW_ONLINE = config.get('steam', 'online') == 'yes'
    settings.AIM_AUTOJOIN_CHAT = config.get('aim', 'autojoin') == 'yes'
    settings.AIM_PASSWORD = config.get('aim', 'password')
    settings.AIM_PROFILE = config.get('aim', 'profile')
    settings.AIM_USERNAME = config.get('aim', 'username')
    nicks.add(settings.AIM_USERNAME)
    settings.PRIVATE_MODULES = config.get('modules', 'private').split(',')
    settings.DETACH = config.get('main', 'detach') == 'yes'
    settings.WORKERS = config.getint('main', 'workers')
    settings.YELP_DEFAULT_LOCATION = config.get('yelp', 'default_location')
    settings.TASKS = []
    if config.get('twitter', 'enabled') == 'yes':
        settings.TASKS.append('tweets')
    settings.TWITTER_CONSUMER_KEY = config.get('twitter', 'username')
    settings.TWITTER_CONSUMER_SECRET = config.get('twitter', 'password')
    try:
        settings.TWITTER_TOKEN_KEY = config.get('twitter', 'token_key')
        settings.TWITTER_TOKEN_SECRET = config.get('twitter', 'token_secret')
    except NoOptionError:
        settings.TWITTER_TOKEN_KEY = None
        settings.TWITTER_TOKEN_SECRET = None
    settings.TWITTER_UPDATE_FREQ = config.getint('twitter', 'updatefreq')
    if config.get('ircops', 'enabled') == 'yes':
        settings.TASKS.append('ircops')
    settings.IRC_GIVE_OPS_FREQ = config.getint('ircops', 'updatefreq')
    settings.HTTP_AGENT = config.get('http', 'agent')
    settings.HTTP_COOKIES = config.get('http', 'cookies') == 'yes'
    settings.HTTP_TIMEOUT = config.getint('http', 'timeout')
    settings.PIDFILE = config.get('main', 'pidfile')
    settings.UPDATER_FREQ = config.getint('updater', 'updatefreq')
    channels = set()
    channels.update(config.get('irc', 'channels').split(','))
    channels.update(config.get('silcplugin', 'channels').split(','))
    channels.add(config.get('gateway', 'channel'))
    channels.add(config.get('updater', 'channel'))
    channels.add(config.get('twitter', 'channel'))
    channels = [channel for channel in channels if channel]

    channels.remove('#madcow')
    if len(channels) > 1:
        channels = validate_list('channels', channels)
    settings.IRC_CHANNELS = channels
    settings.SILC_CHANNELS = channels
    settings.TWITTER_CHANNELS = 'ALL'
    settings.GATEWAY_CHANNELS = 'ALL'
    settings.UPDATER_ANNOUNCE_CHANNELS = 'ALL'
    if config.get('updater', 'enabled') == 'yes':
        settings.TASKS.append('updater')
    settings.LOG_PUBLIC = config.get('main', 'logpublic') == 'yes'
    settings.IGNORE_NICKS = config.get('main', 'ignoreList').split(',')
    settings.LOGGING_LEVEL = config.get('main', 'loglevel')
    settings.LOGGING_ENCODING = settings.ENCODING = config.get('main', 'charset')
    settings.OWNER_NICK = config.get('main', 'owner')
    settings.ALIASES = config.get('main', 'aliases').split(',')
    settings.SILC_DELAY = config.getint('silcplugin', 'delay')
    settings.SILC_HOST = config.get('silcplugin', 'host')
    settings.SILC_PORT = config.getint('silcplugin', 'port')
    settings.SILC_RECONNECT = config.get('silcplugin', 'reconnect') == 'yes'
    settings.SILC_RECONNECT_WAIT = config.getint('silcplugin', 'reconnectWait')
    settings.SMTP_FROM = config.get('smtp', 'sender')
    settings.SMTP_PASS = config.get('smtp', 'password')
    settings.SMTP_SERVER = config.get('smtp', 'server')
    settings.SMTP_USER = config.get('smtp', 'user')
    settings.GATEWAY_ADDR = config.get('gateway', 'bind')
    settings.GATEWAY_ENABLED = config.get('gateway', 'enabled') == 'yes'
    settings.GATEWAY_IMAGE_PATH = config.get('gateway', 'imagePath')
    settings.GATEWAY_IMAGE_URL = config.get('gateway', 'imageURL')
    settings.GATEWAY_PORT = config.getint('gateway', 'port')
    settings.GATEWAY_SAVE_IMAGES = settings.GATEWAY_IMAGE_URL and settings.GATEWAY_IMAGE_PATH
    settings.ADMIN_ENABLED = config.get('admin', 'enabled') == 'yes'
    settings.ALLOW_REGISTRATION = config.get('admin', 'allowRegistration') == 'yes'
    settings.DEFAULT_FLAGS = config.get('admin', 'defaultFlags')
    settings.DELICIOUS_USERNAME = config.get('delicious', 'username')
    settings.DELICIOUS_PASSWORD = config.get('delicious', 'password')
    nicks = [nick for nick in set(nicks) if nick]
    if len(nicks) > 1:
        print 'Multiple nicks found, pick one to use:'
        for i, nick in enumerate(nicks):
            print '%d %s' % (i + 1, nick)
        while True:
            i = raw_input('>>> ')
            try:
                nick = nicks[int(i) - 1]
                break
            except:
                pass
    else:
        nick = nicks[0]
    settings.BOTNAME = nick

    with open(os.path.join(todir, 'settings.py'), 'wb') as fp:
        for key in sorted(dir(settings)):
            if key.isupper():
                val = getattr(settings, key)
                if val == '':
                    val = None
                out = None
                if isinstance(val, list):
                    val = [_ for _ in val if _]
                    if val:
                        out = dumplist(val, key, 80)
                if not out:
                    out = '%s = %r' % (key, val)
                print >> fp, out
    print 'wrote settings.py'

    dbdir = os.path.join(todir, 'db')
    namespace = config.get('modules', 'dbNamespace')

    def get_dbfile(file):
        valid_namespace = False
        name = None
        try:
            basedir, filename = os.path.split(file)
            filename = filename.replace('.db', '')
            key, this_namespace, name = filename.split('-')
            if this_namespace != namespace:
                raise ValueError
            valid_namespace = True
            for ext in '', '.db':
                test = os.path.join(basedir, filename + ext)
                try:
                    db = dbm.open(test, 'r')
                except:
                    continue
                db.close()
                return test, name, 'dbm'
        except:
            pass
        if valid_namespace and name:
            return file, name, 'txt'

    if data is not None:
        for filename in os.listdir(data):
            src = os.path.join(data, filename)
            if os.path.isfile(src):
                try:
                    src, name, type = get_dbfile(src)
                except ValueError:
                    continue

                if type == 'dbm':
                    dst = os.path.join(dbdir, name)
                    db = dbm.open(src, 'r')
                    try:
                        new = dbm.open(dst, 'c', 0640)
                        try:
                            print 'copying %d items for %s database' % (len(db), name)
                            for key in db.keys():
                                new[key] = db[key]
                        finally:
                            new.close()
                    finally:
                        db.close()
                elif type == 'txt':
                    dst = os.path.join(dbdir, name)
                    shutil.copy(src, dst)
                    print 'copied %s' % name

            elif os.path.isdir(src) and filename == 'megahal':
                seen = set()
                megahal_from = src
                megahal_to = os.path.join(dbdir, filename)
                for basedir, subdirs, filenames in os.walk(megahal_from):
                    for filename in filenames:
                        if filename in BRAIN_FILES:
                            src = os.path.join(basedir, filename)
                            dstpath = src.replace(megahal_from + os.sep, '')
                            dst = os.path.join(megahal_to,  dstpath)
                            dstdir, dstfile = os.path.split(dst)
                            if not os.path.exists(dstdir):
                                os.makedirs(dstdir)
                            shutil.copy(src, dst)
                            print 'copied %s' % dstpath

    # memebot needs migration too since we ditched sqlobject
    try:
        migrate_memebot(config, dbdir, fromdir)
    except Exception, error:
        print >> sys.stderr, "couldn't migrate memebot: %s" % error

    src = os.path.join(fromdir, 'logs')
    if os.path.isdir(src):
        print 'copying logs'
        logdir = os.path.join(todir, 'log')
        os.makedirs(logdir)
        dst = os.path.join(logdir, 'public')
        main_log = []
        name = 'madcow.log'
        count = [0]
        def check(basedir, filenames):
            count[0] += len(filenames)
            if name in filenames:
                main_log.append(os.path.join(basedir, name))
                count[0] -= 1
                return [name]
            return []
        shutil.copytree(src, dst, ignore=check)
        print 'copied %d public logs' % count[0]
        if main_log:
            copy(main_log[0], os.path.join(logdir, name))


def migrate_memebot(config, dbdir, fromdir):
    # XXX hack to work around busted pysqlite/sqlobject integration
    try:
        from pysqlite2 import _sqlite
        if _sqlite.sqlite_version.count('.') == 3:
            i = _sqlite.sqlite_version.rindex('.')
            _sqlite.sqlite_version = _sqlite.sqlite_version[:i]
    except ImportError:
        pass

    import sqlobject

    class URL(sqlobject.SQLObject):

        class sqlmeta:

            table = 'url'

        url = sqlobject.StringCol()
        clean = sqlobject.StringCol()
        author = sqlobject.ForeignKey('Author')
        channel = sqlobject.ForeignKey('Channel')
        citations = sqlobject.IntCol(default=0)
        posted = sqlobject.DateTimeCol(default = datetime.now)
        comments = sqlobject.MultipleJoin('Comments')


    class Author(sqlobject.SQLObject):

        name = sqlobject.StringCol(alternateID=True, length=50)
        urls = sqlobject.MultipleJoin('URL')
        comments = sqlobject.MultipleJoin('Comments')
        points_new = sqlobject.IntCol(default=0)
        points_old = sqlobject.IntCol(default=0)
        points_credit = sqlobject.IntCol(default=0)


    class Channel(sqlobject.SQLObject):

        name = sqlobject.StringCol(alternateID=True, length=50)
        urls = sqlobject.MultipleJoin('URL')


    class Comments(sqlobject.SQLObject):

        text = sqlobject.StringCol()
        author = sqlobject.ForeignKey('Author')
        url = sqlobject.ForeignKey('URL')

    engine = config.get('memebot', 'db_engine')
    uri = engine + '://'
    if engine == 'sqlite':
        namespace = config.get('modules', 'dbNamespace')
        uri += os.path.join(fromdir, 'data/db-%s-memes' % namespace)
    else:
        user = config.get('memebot', 'db_user')
        dbpass = config.get('memebot', 'db_pass')
        if dbpass:
            user += ':' + dbpass
        host = config.get('memebot', 'db_host')
        if not host:
            host = 'localhost'
        db_port = config.get('memebot', 'db_port')
        if db_port:
            host += ':' + config.db_port
        uri += '%s@%s/%s' % (user, host, config.get('memebot', 'db_name'))

    connection = sqlobject.connectionForURI(uri)
    raw = connection.getConnection()
    cursor = raw.cursor()

    db = shelve.open(os.path.join(dbdir, 'memebot'), writeback=True)
    db['urls'] = {}
    db['nicks'] = {}

    count = cursor.execute(
            '''
            SELECT      u.url AS orig,
                        u.clean AS clean,
                        a.name AS author,
                        c.name AS channel,
                        u.citations AS count,
                        u.posted AS date
            FROM        url u,
                        author a,
                        channel c
            WHERE       u.author_id = a.id AND
                        u.channel_id = c.id
            '''
            )
    print 'memebot: copying %d urls' % count
    for orig, clean, author, channel, count, date in cursor.fetchall():
        db['urls'][clean] = {
                'orig': orig,
                'date': date,
                'count': count,
                'channel': channel,
                'nick': author,
                }
    count = cursor.execute(
            '''
            SELECT      name AS nick,
                        points_new AS new,
                        points_old AS old,
                        points_credit AS credit
            FROM        author
            '''
            )
    print 'memebot: copying %d authors' % count
    for nick, new, old, credit in cursor.fetchall():
        db['nicks'][nick] = {'new': new, 'old': old, 'credit': credit}
    db.close()


def dumplist(obj, name, max):
    last = len(obj) - 1
    lines = [['%s = [' % name]]
    isize = pos = len(lines[0][0])
    indent = ' ' * isize
    for i, item in enumerate(obj):
        val = repr(item) + (']' if i == last else ', ')
        size = len(val)
        if pos + size > max:
            lines.append([indent])
            pos = isize
        lines[-1].append(val)
        pos += size
    return '\n'.join(''.join(line).rstrip() for line in lines)


def main(argv=None):
    optparse = OptionParser('%prog <fromdir> <todir>', version=__version__, description=__doc__)
    opts, args = optparse.parse_args(argv)
    if len(args) != 2:
        optparse.print_help()
        return 2
    fromdir, todir = args
    if not os.path.isdir(fromdir):
        optparse.error("%s does not exist or is not a directory" % fromdir)
    if os.path.exists(todir):
        optparse.error('%s already exists' % todir)
    try:
        migrate(fromdir, todir)
    except Exception, error:
        print >> sys.stderr, 'error: %s' % error
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
