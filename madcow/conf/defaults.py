"""Settings for madcow"""

###################
### MAIN CONFIG ###
###################

PROTOCOL = 'cli'  # irc, aim, pysilc, shell, cli
BOTNAME = 'madcow'  # will use this nickname in irc/silc and for addressing
ALIASES = ['!']  # list of other nicks the bot will also respond to
DETACH = False  # set to True to run as a daemon (UNIX only)
WORKERS = 5  # how many threads to process requests
LOG_PUBLIC = True  # set to False to avoid logging public chatter
LOG_BY_DATE = True  # set to False to have channel logs all one file instead of split by day
IGNORE_NICKS = ['spammer', 'otherbot']  # list of nicknames to completely ignore
IGNORE_REGEX = ['NOBOT', 'my\.secret\.domain']  # regular expressions that if they match on input text, will be ignored by the bot. this is handy to prevent certain urls being broadcast to delicious, if you have that enabled.
PIDFILE = 'madcow.pid'  # file (relative to base) for pid for current bot
ENCODING = 'utf-8'  # default character set, None for auto (generally utf-8)
OWNER_NICK = 'yournick'  # in irc/silc/aim set to your name to be given auto-admin
ALLOW_REGISTRATION = True  # allow other users to register with the bot
DEFAULT_FLAGS = ''  # flags given to registered users o=auto-op (irc only), a=admin
PRIVATE_HELP = True  # if True, redirects "help" output to private message

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
           'bbcnews',             # bbc news headlines
           'beer',                # beer
           'calc',                # google calculator
           'clock',               # world clock
           'cnn',                 # show cnn headline
           'dictionary',          # definition of words
           'election',            # current electoral vote predictor for 2008 US election
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
           'translate',           # language translations
           'urban',               # look up word/phrase on urban dictionary
           'weather',             # look up weather from wunderground
           'wikimedia',           # look up summaries from various wikis
           'wikiquotes',          # look up quotes from wikiquotes
           'yelp',                # get restaraunt rating/address
           'youtube',             # scrape youtube titles
           'staff',               # mark users as 'staff'
           'company',             # set company name for nick (req. staff module)
           'realname',            # set real name for nick (req. staff module)
           'notes',               # add a note to a nick (req. staff module)
           'xray',                # see all staff-set data on a nick (req. staff module)
           'blog',                # get the latest blog posts from RSS feed (specify URL below)
           'links',               # create shortcut links (req. staff module)
           'welcome',             # send a user a welcome message (set message below)
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
           #'jinx',                # someone owes you a coke for being unoriginal
           #'joke',                # random joke
           #'karma',               # keep track of karma (nick++, nick--)
           #'livejournal',         # get livejournal entries (random or by nick)
           #'lyrics',              # look up song lyrics (spammy!)
           #'megahal',             # markov bot (requires you build C extension!)
           #'memebot',             # track urls and lay smackdown on old memes
           #'obama',               # countdown since change.. such as it has been
           #'pollmail',            # poll an email account using IMAP for messages to echo to IRC
           #'roll',                # roll ad&d dice
           #'slut',                # how slutty is the phrase? (safesearch vs. regular)
           #'steam',               # allow queries into your steam group about who's online
           #'terror',              # current status of TERROR
           #'texts',               # random texts from last night
           #'trek',                # generate star trek technobabble
           #'webtender',           # how to make drinks!
           #'woot',                # latest woot offer
           #'djmemebot',           # memebot's django app backend integration
           #'wunderground',        # advanced weather api access, (needs api key from wunderground.com)
           #'wolfram',             # wolfram alpha api access (see WOLFRAM_* settings below if you enable this)
           ]

# these are modules that run on their own periodically if enabled. settings are below
TASKS = [
        #'ircops',                 # automatically provide ops in irc
        #'pollmail'                # automatically poll imap mail
        #'tweets',                 # gateway for tweet timeline
        ]

PRIVATE_MODULES = ['lyrics', 'company', 'realname', 'notes', 'xray']  # list of modules (from MODULES above) that only respond in private message

# Blacklist mechanism to disable modules when "better" ones are enabled, as
# defined here. The master module is the dictionary key, and its subservients
# are in the list. In the default below, for example, enabling wunderground.py
# will force noaa.py and weather.py to unload. They have conflicting triggers,
# as well as basically do the same thing. wunderground.py is the superior
# plugin, however it requires one to enroll for (free) API access, which may
# not be to everyone's taste or means.
MODULE_SUPERCEDES = {'wunderground': ['noaa', 'weather']}
TASK_SUPERCEDES = {}

#######################
### PROTOCOL CONFIG ###
#######################

# connection settings for irc plugin
IRC_HOST = 'localhost'
IRC_PORT = 6667
IRC_SSL = False
IRC_DEBUG = False  # enable for lots of details. noisy!
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
IRC_GIVE_OPS_FREQ = 30

# settings for the aim protocol
AIM_USERNAME = 'aimusername'
AIM_PASSWORD = 'aimpassword'
AIM_PROFILE = 'Madcow InfoBot'
AIM_AUTOJOIN_CHAT = True
AIM_AUTOJOIN_LEVEL = 'o'  # who to accept invites from. o=owner, a=admin, r=registered, *=anyone. owner is set with OWNER_NICK above, the others are handled via internal admin management. the bot will always accept invites from owner.

# settings for the silc protocol
SILC_CHANNELS = ['#madcow']
SILC_HOST = 'localhost'
SILC_PORT = 706
SILC_PASSPHRASE = None
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
DELICIOUS_AUTH_TYPE = 'http'  # http or oauth
# http username/password
DELICIOUS_USERNAME = None
DELICIOUS_PASSWORD = None
# oauth tokens (run contrib/get_delicious_auth_keys.py to get this)
DELICIOUS_CONSUMER_KEY = None
DELICIOUS_CONSUMER_SECRET = None
DELICIOUS_TOKEN_KEY = None
DELICIOUS_TOKEN_SECRET = None
DELICIOUS_SESSION_HANDLE = None

# for the yelp plugin
YELP_DEFAULT_LOCATION = 'San Francisco, CA'

# for the blog plugin
BLOG_RSS_URL = 'http://www.activestate.com/blog/rss.xml'

# for the welcome plugin
WELCOME_MSG = 'Have a good time!'

# for pollmail plugin
POLLMAIL_FREQUENCY = 60
POLLMAIL_USE_PASSWORD = False
POLLMAIL_PASSWORD = None
POLLMAIL_AUTOSTART = False
POLLMAIL_JSON_REGEX = r'{({.+})}'
IMAP_SERVER = 'localhost'
IMAP_PORT = 993
IMAP_USERNAME = None
IMAP_PASSWORD = None
IMAP_USE_SSL = True

# for wolfram alpha api access
WOLFRAM_API_APPID = None  # you need to sign up at wolframalpha.com and register for free api access
WOLFRAM_API_URL = None  # only change this to override the standard api access url

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
TWITTER_CONSUMER_KEY = None
TWITTER_CONSUMER_SECRET = None
TWITTER_ACCESS_TOKEN_KEY = None
TWITTER_ACCESS_TOKEN_SECRET = None
TWITTER_UPDATE_FREQ = 45
TWITTER_OUTPUT = 'ALL'
TWITTER_TWEET_FORMAT = u'>> tweet from {tweet.user.screen_name}: {tweet.text_clean} <<'
TWITTER_DISABLE_CACHE = True
TWITTER_ERR_ANNOUNCE = True
TWITTER_ERR_ANNOUNCE_FREQ = 28800
TWITTER_SOFT_LIMIT = 10

# settings for modules that use http
HTTP_TIMEOUT = 10
HTTP_AGENT = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'
HTTP_COOKIES = True

# for django memebot integration
DJMEMEBOT_SETTINGS_FILE = '/path/to/memebot/settings.py'

# for weather underground module: note: need an api key (api.wunderground.com)
# to enable this, you must add/uncomment the module "wunderground" first.
WUNDERGROUND_API_KEY = 'FILLMEIN'
WUNDERGROUND_LANG = 'EN'
WUNDERGROUND_PREFER_METRIC = False
WUNDERGROUND_PRIMARY_ONLY = False
WUNDERGROUND_API_SCHEME = 'http'
WUNDERGROUND_API_NETLOC = 'api.wunderground.com'
WUNDERGROUND_DO_COLOR = True
WUNDERGROUND_USER_AGENT = None
WUNDERGROUND_TIMEOUT = 10
