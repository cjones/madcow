"""Settings for madcow"""

###################
### MAIN CONFIG ###
###################

PROTOCOL = 'cli'  # irc, slack, aim, pysilc, shell, cli
BOTNAME = 'madcow'  # will use this nickname in irc/silc and for addressing
ALIASES = ['!']  # list of other nicks the bot will also respond to
DETACH = False  # set to True to run as a daemon (UNIX only)
WORKERS = 5  # how many threads to process requests
LOG_PUBLIC = True  # set to False to avoid logging public chatter
LOG_BY_DATE = True  # set to False to have channel logs all one file instead of split by day
IGNORE_NICKS = ['spammer', 'otherbot']  # list of nicknames to completely ignore
IGNORE_REGEX = ['NOBOT', 'my\.secret\.domain']  # regular expressions that if they match on input text, will be ignored by the bot
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

MODULES = [
        'alias',               # allow users to make command aliases
        'area',                # look up area codes
        'artfart',             # random ascii art
        'bash',                # bash (irc/im) quotes
        'bbcnews',             # bbc news headlines
        'calc',                # google calculator
        'care',                # generate a high-precision care-o-meter
        'chuck',               # gets a random chuck norris fact
        'dictionary',          # definition of words
        'factoids',            # makes madcow remember stuff from chatter
        'figlet',              # generate ascii fonts
        'google',              # i'm feeling lucky query
        'grufti',              # random response triggeres, like grufti bot
        'jinx',                # someone owes you a coke for being unoriginal
        'joke',                # random joke
        'karma',               # keep track of karma (nick++, nick--)
        'learn',               # used for various modules to cache per-user data
        'livejournal',         # get livejournal entries (random or by nick)
        'lyrics',              # look up song lyrics (spammy!)
        'megahal',             # markov bot (requires you build C extension!)
        'memebot',             # track urls and lay smackdown on old memes
        'nslookup',            # look up ip of hostnames
        'roll',                # roll ad&d dice
        'seen',                # keep track of last thing everyone in channel said
        'slut',                # how slutty is the phrase? (safesearch vs. regular)
        'spellcheck',          # spellcheck a word/phrase using google
        'stockquote',          # get yahoo stock quotes
        'trek',                # generate star trek technobabble
        'weather',             # look up weather from wunderground
        'webtender',           # how to make drinks!
        'wikihow',             # mashup instructions from wikihow
        'wikimedia',           # look up summaries from various wikis
        'wikiquotes',          # look up quotes from wikiquotes
        'woot',                # latest woot offer
        'youtube',             # scrape youtube titles

        ## requires configuration below
        #'wolfram',             # wolfram alpha api access (see WOLFRAM_* settings below if you enable this)
        #'summon',              # summon users (send email/sms)
        #'steam',               # allow queries into your steam group about who's online
        #'pollmail',            # poll an email account using IMAP for messages to echo to IRC
        #'djmemebot',           # memebot's django app backend integration

        ## ActiveState company modules
        #'blog',                # get the latest blog posts from RSS feed (specify URL below)
        #'company',             # set company name for nick (req. staff module)
        #'links',               # create shortcut links (req. staff module)
        #'notes',               # add a note to a nick (req. staff module)
        #'realname',            # set real name for nick (req. staff module)
        #'staff',               # mark users as 'staff'
        #'welcome',             # send a user a welcome message (set message below)
        #'xray',                # see all staff-set data on a nick (req. staff module)

        ## currently broken
        #'beer',                # beer
        #'bible',               # get a quote from the bible
        #'clock',               # world clock
        #'cnn',                 # show cnn headline
        #'election',            # current electoral vote predictor for 2008 US election
        #'fmylife',             # fmylife complaint, random or by ID
        #'movie',               # rate movie on imdb & rotten tomatoes
        #'sunrise',             # get sunrise/sunset from google for your area
        #'texts',               # random texts from last night
        #'translate',           # language translations
        #'urban',               # look up word/phrase on urban dictionary
        #'yelp',                # get restaraunt rating/address
        ]

# these are modules that run on their own periodically if enabled. settings are below
TASKS = [
        #'ircops',                 # automatically provide ops in irc
        #'pollmail'                # automatically poll imap mail
        #'tweets',                 # gateway for tweet timeline
        ]

# list of modules (from MODULES above) that only respond in private message
PRIVATE_MODULES = ['company', 'realname', 'notes', 'xray'] 

MODULE_SUPERCEDES = {}
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

# settings for slack protocol
SLACK_TOKEN = ''
SLACK_CHANNELS = ['general']

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

# for the yelp plugin
YELP_DEFAULT_LOCATION = 'San Francisco, CA'

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

# for outgoing emails like summon
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

# for the blog plugin
BLOG_RSS_URL = 'http://www.activestate.com/blog/rss.xml'

# for the welcome plugin
WELCOME_MSG = 'Have a good time!'
