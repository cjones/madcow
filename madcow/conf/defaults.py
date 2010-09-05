"""Settings for madcow"""

###################
### MAIN CONFIG ###
###################

PROTOCOL = 'cli'  # irc, aim, silc, shell, cli
BOTNAME = 'madcow'  # will use this nickname in irc/silc and for addressing
ALIASES = ['!']  # list of other nicks the bot will also respond to
DETACH = False  # set to True to run as a daemon (UNIX only)
WORKERS = 5  # how many threads to process requests
LOG_PUBLIC = True  # set to False to avoid logging public chatter
IGNORE_NICKS = ['spammer', 'otherbot']  # list of nicknames to completely ignore
PIDFILE = 'madcow.pid'  # file (relative to base) for pid for current bot
ENCODING = 'utf-8'  # encoding of your system or the protocol you are communicating over
OWNER_NICK = 'yournick'  # in irc/silc/aim set to your name to be given auto-admin
ALLOW_REGISTRATION = True  # allow other users to register with the bot
DEFAULT_FLAGS = ''  # flags given to registered users o=auto-op (irc only), a=admin

###############
### LOGGING ###
###############

LOGGING_LEVEL = 'INFO'  # DEBUG, INFO, WARN, ERROR
LOGGING_FORMAT = '[%(time)s - %(level)s] %(message)s'
LOGGING_TIME_FORMAT = '%Y/%m/%d %H:%M:%S'
LOGGING_ENCODING = ENCODING
UNIQUE_TIMESTAMP_FORMAT = '%Y%m%d'
UNIQUE_MAX_FILES = 1000

###############
### MODULES ###
###############

MODULES = ['alias',               # allow users to make command aliases
           'area',                # look up area codes
           'babel',               # language translations
           'bbcnews',             # bbc news headlines
           'calc',                # google calculator
           'clock',               # world clock
           'cnn',                 # show cnn headline
           'dictionary',          # definition of words
           'election2008',        # current electoral vote predictor for 2008 US election
           'google',              # i'm feeling lucky query
           'learn',               # used for various modules to cache per-user data
           'movie',               # rate movie on imdb & rotten tomatoes
           'noaa',                # alternative to wunderground (us-only, more accurate)
           'nslookup',            # look up ip of hostnames
           'seen',                # keep track of last thing everyone in channel said
           'spellcheck',          # spellcheck a word/phrase using google
           'stockquote',          # get yahoo stock quotes
           'summon',              # summon users (send email/sms)
           'sunrise',             # get sunrise/sunset from google for your area
           'urban',               # look up word/phrase on urban dictionary
           'weather',             # look up weather from wunderground
           'wikimedia',           # look up summaries from various wikis
           'wikiquotes',          # look up quotes from wikiquotes
           'yelp',                # get restaraunt rating/address
           #
           # the following modules are either silly, or potentially annoying/offensive.
           # they are disabled by default so you can make the decision about how
           # obnoxious your bot is able to be.
           #
           #'artfart',             # random ascii art
           #'bash',                # bash (irc/im) quotes
           #'bible',               # get a quote from the bible
           #'care',                # generate a high-precision care-o-meter
           #'chp',                 # california real-time traffic reports
           #'delicious',           # post all urls to delicious (see config below)
           #'factoids',            # makes madcow remember stuff from chatter
           #'figlet',              # generate ascii fonts
           #'fmylife',             # fmylife complaint, random or by ID
           #'grufti',              # random response triggeres, like grufti bot
           #'hugs',                # random group hug confession
           #'jinx',                # someone owes you a coke for being unoriginal
           #'joke',                # random joke
           #'karma',               # keep track of karma (nick++, nick--)
           #'livejournal',         # get livejournal entries (random or by nick)
           #'lyrics',              # look up song lyrics (spammy!)
           #'megahal',             # markov bot (requires you build C extension!)
           #'memebot',             # track urls and lay smackdown on old memes
           #'obama',               # countdown since change.. such as it has been
           #'roll',                # roll ad&d dice
           #'slut',                # how slutty is the phrase? (safesearch vs. regular)
           #'steam',               # allow queries into your steam group about who's online
           #'texts',               # random texts from last night
           #'trek',                # generate star trek technobabble
           #'war',                 # current war status
           #'wardb',               # look up warhammer online items and show stats
           #'webtender',           # how to make drinks!
           #'woot',                # latest woot offer
           ]

PRIVATE_MODULES = ['lyrics']  # list of modules (from MODULES above) that only respond in private message

#######################
### PROTOCOL CONFIG ###
#######################

# connection settings for irc plugin
IRC_HOST = 'localhost'
IRC_PORT = 6667
IRC_SSL = False
IRC_PASSWORD = None
IRC_CHANNELS = ['#madcow']
IRC_RECONNECT = True
IRC_RECONNECT_WAIT = 3
IRC_RECONNECT_MESSAGE = None
IRC_REJOIN = True
IRC_REJOIN_WAIT = 3
IRC_REJOIN_MESSAGE = None
IRC_QUIT_MESSAGE = None
IRC_OPER = False
IRC_OPER_USER = None
IRC_OPER_PASS = None
IRC_IDENTIFY_NICKSERV = False
IRC_NICKSERV_USER = 'NickServ'
IRC_NICKSERV_PASS = None
IRC_FORCE_WRAP = 400
IRC_DELAY_LINES = 0  # miliseconds
IRC_KEEPALIVE = True
IRC_KEEPALIVE_FREQ = 30
IRC_KEEPALIVE_TIMEOUT = 120
IRC_GIVE_OPS = False
IRC_GIVE_OPS_FREQ = 30

# settings for the aim protocol
AIM_USERNAME = 'aimusername'
AIM_PASSWORD = 'aimpassword'
AIM_PROFILE = 'Madcow InfoBot'
AIM_AUTOJOIN_CHAT = True

# settings for the silc protocol
SILC_CHANNELS = ['#madcow']
SILC_HOST = 'localhost'
SILC_PORT = 706
SILC_RECONNECT = True
SILC_RECONNECT_WAIT = 3
SILC_DELAY = 350  # miliseconds

#######################
### MODULE SETTINGS ###
#######################

# for steam plugin
STEAM_GROUP = None
STEAM_SHOW_ONLINE = True

# for delicious plugin
DELICIOUS_USERNAME = None
DELICIOUS_PASSWORD = None

# for the yelp plugin
YELP_DEFAULT_LOCATION = 'San Francisco, CA'

################
### FEATURES ###
################

SMTP_SERVER = 'localhost'
SMTP_FROM = 'madcow@example.com'
SMTP_USER = None
SMTP_PASS = None

# a gateway for communicating with the bot over tcp
GATEWAY_ENABLED = False
GATEWAY_ADDR = 'localhost'
GATEWAY_PORT = 5000
GATEWAY_CHANNELS = 'ALL'  # or list of channels
GATEWAY_SAVE_IMAGES = False
GATEWAY_IMAGE_PATH = '/tmp/images'
GATEWAY_IMAGE_URL = 'http://example.com/images/'

# watch a twitter account and bridge tweets to channels you are in
TWITTER_ENABLED = False
TWITTER_CONSUMER_KEY = None
TWITTER_CONSUMER_SECRET = None
TWITTER_TOKEN_KEY = None
TWITTER_TOKEN_SECRET = None
TWITTER_UPDATE_FREQ = 45
TWITTER_CHANNELS = 'ALL'  # or list of channels

# settings for modules that use http
HTTP_TIMEOUT = 10
HTTP_AGENT = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'
HTTP_COOKIES = True

# check for madcow updates once a day and announce new versions in channel
UPDATER_ENABLED = True
UPDATER_FREQ = 86400
UPDATER_ANNOUNCE_CHANNELS = 'ALL'  # or list of channels

# watch world of warcraft armory rss feed and report events to channel
WOW_ARMORY_FEED_ENABLED = False
WOW_ARMORY_FEED_FREQ = 300
WOW_ARMORY_CHANNELS = 'ALL'  # or list of channels
