=Overview=

Madcow is an extensible IRC bot, with support for AIM and SILC protocols, invocation from the command-line, and embedding within ipython for ease of plugin development. It is modeled loosely on a mish-mash of venerable bots of yore: infobot, grufti, eggdrop, etc., though with less emphasis on channel management. It ships with a large set of plugins to form its base functionality as well as offering an API to craft your own.

=Requirements=

  * Python 2.7 or higher (2.6 *might* work, but I do not test this).
  * Various optional components have dependencies you must satisfy should you wish to use them:
    - To use the SILC protocol, you will need to install the silc-toolkit and pysilc libraries.
    - To embed madcow within a running ipython interpreter, you need ipython. Obviously.
    - See the Features section for more detail on how to configure/enable various plugins.

=Caveats/Warnings=

1. This bot can be *spammy* as well as produce content *not suitable for a work environment* if not configured properly. I've attempted to make the defaults reasonable (bot requires explicit addressing, potentially offensive plugins such as urban dictionary disabled, etc.) but this is an afterthought/courtesy more than a promise. I am not responsible for any trouble you get yourself into. Join it to a private channel and judge for yourself before bringing it into work IRC, and be aware that different chat environments have wildly different levels of tolerance for chatty bots. Know your audience.

2. Many of the data sources are *scraped*, as an API is either not available or is generally a pain to set up. An unfortunate reality of scraping websites is that this kind of code is fragile and prone to breaking if/when the site owner makes changes to the layout or design. Feel free to report this in tickets, but I tend to fix them when I fix them and not before. Fixing broken modules and submitting a patch is a great way to get it done faster. :)

=Features=

Madcow has accumlated a fair amount of features that require a little more setup than the basic triggered query/response plugins. Some of these are undocumented currently, but you may email me asking for guidance if you run into trouble configuring these. Some examples of modules that don't "just work" without more care/feeding/setup:

  * Authenticated IRC auto-opping. I actually discourage use of this, as it is not nearly robust enough compared to other bots or Services. But, it's there if you wish to use it..Requires some account setup with the ADMIN subcommand.

  * 2-way SMS to IRC message relay (and attached photo capture). This uses a local gateway port and a specific syntax. You might also interact with this by invoking a script with procmail. Unfortunately, this is undocumented at this time, but I am more than happy to explain its usage upon request.

  * Twitter to IRC message relay. Requires a twitter oAuth key. There is a tool in the contrib directory to help ease the pain of this task, but it's still a PITA. Blame Twitter.

  * URL tracking software:
    - Via delicious, this requires oAuth configuration with Yahoo's API, same as Twitter.
    - Saved locally to a database: requires postgresql or mysql, and django config to use the UI or generate RSS.

  * A module to emulate grufti's match/response file syntax is provided, but this syntax is not documented, though more or less straightforward.

  * MegaHAL, a 5th order markov response bot. This is actually some ancient C code I didn't write. If you enable megahal, Madcow will attempt to compile the cmegahal.so/dylib core on first run. This may not work for you, depending on your platform and environment. You are sort of on your own debugging compilation issues with megahal. As of this writing, it compiles cleanly on Ubuntu 12.04 precise -- both 32 and 64bit architecture -- provided that you have build-essentials package installed from APT. Beyond that, I have not tested it so YMMV. In theory it should compile anywhere (there are even macros for Amiga!). But it is really old, so do not be surprised if it blows up instead.

  * The (Valve) Steam plugin, which shows friend's play status but does *not* currently bridge messages, requires a group/community be created and for players you wish to track to be a member of this group.

  * The summon module uses email, the intention being to use SMS-email gateway addresses. You set these via the "learn" module, which is a key/value store tied to the user invoking the bot. See the help for learn.py for syntax. Also see [http://en.wikipedia.org/wiki/List_of_SMS_gateways List of SMS gateways]. You will need a configured MTA capable of internet delivery. Be aware that many ISPs pre-emptively filter SMTP ports to discourage infected hosts from being open relays, so this may not be possible, depending on where you are running it. You can try using google's TLS/SSL email server, or one your ISP provides. I am unable to provide support for this.

=Modules=

Madcow ships with the following modules, which can be enabled/disabled in config, as well as a template for easily creating your own (requires at least basic Python proficiency):

    * alias - Arbitrarily assign triggers to short-cut text.
    * area - Look up the provided area code (US only)
    * artfart - Random ASCII art, usually offensive.
    * bash - Search bash.org or QDB for provided query or return a random quote. Sometimes offensive or off-color.
    * bbcnews - Search or get headline from BBC headline news.
    * bible - Display the select bible chapter/verse range in the selected translation. Note: fiction.
    * calc - Use Google's calculator function.
    * care - Silly thing. It's an AA care-o-meter. It also has an inappropriate alternate invocation that's very NSFW.
    * chp - Detailed highway information for California (US).
    * clock - Well, it tells you what time it is. Anywhere. (Uses google's "time in <location>" infobox).
    * cnn - Like bbcnews, but less British and more stupid.
    * delicious - Enable tracking of URLs posted in public, requires oAuth setup.
    * dictionary - Get definition of a word. English only.
    * djmemebot - Bridge to the django URL tracking front-end. Requires a database and Django install.
    * election - Out of date module providing real-time election data (US only). May become active again for 2012.
    * factoids - A port of infobot's "factoid" feature. AKA a huge mess of regex doing NLP poorly. Mostly for Nostalgia
    * figlet - It makes your text really big. Warning: Annoying.
    * fmylife - Random quote from fmylife. Occasionally off-color.
    * google - Returns the URL for an I'm feeling lucky query.
    * grufti - Emulates Grufti match/response file syntax.
    * hugs - Random quote from grouphug.us: Occasionally off-color. Usually fake.
    * jinx - For fun, it informs losers of this childhood game to whom they owe a coke.
    * joke - Random joke. Warning: Unfunny. Offensive.
    * karma - Emulates an infobot feature, increase/decrease a user's karma with ++/--
    * learn - Key/Value store for user meta data, used by various modules to remember emails/locations.
    * livejournal - Random or requested LJ. Note: 85% of LJs are in Russian, making random suck (unless you are Russian)
    * lyrics - Spews lyrics for the requested song. Note: Often inaccurate. It's a wiki. Feel free to go fix them.
    * megahal - 5th order markov bot. It is sort of brilliant if you can get it to work (requires some compiling).
    * memebot - I don't think this actually works anymore..? Oops. Ignore it.
    * movie - Get IMDB/RottenTomato/MetaCritic scores of movies, or list current top office/grossing movies.
    * noaa - Deprecated (see weather.py), returns NOAA weather data for the location (US only)
    * nslookup - DNS.
    * obama - Was once a countdown to inauguration, but is now a counter of time passed since then. Sort of useless.
    * roll - Roll arbitrary (and physically impossible) saving throws.
    * seen - This module keeps track of the last thing everyone said, you may query it for this by user nick.
    * slut - Time waster, it compares the results of safe search vs. raw search to calculate a sluttiness rating.
    * spellcheck - It.. checks your spelling. Uses google. Usually accurate, but don't base a term paper on it.
    * steam - Displays the current status of all members of a community/group.
    * stockquote - Real time (-ISH, 15 minute delay for free ticker) stock prices.
    * summon - Sends email w/ optional message to the user specific, if their email is on record with learn.py
    * sunrise - Get the exact sunrise/sunset for the specified location (global).
    * terror - Some handy threat level information. Never forget.
    * texts - Random crap from "texts from last night". NSFW.
    * translate - Translate between 2 arbitray languages, with auto-detection. Uses google.
    * trek - Generate random technobabble.
    * urban - Look up the phrase on urban dictionary (almost always offensive and highly inappropriate for work).
    * weather - Provide 3 weather views: forcecast, NOAA (airport/official weather), and PWS (personal weather station)
    * webtender - Query instructions for mixed drinks.
    * wikimedia - Allows article lookup for various wikis. Notably wikipedia, but conservapedia and others for laughs.
    * wikiquotes - Like wikimedia but tuned to work with wikiquotes website.
    * woot - List the current woot-off (I am not sure the point of this, but it's there. If you need it.)
    * yelp - Look up rating for the specified store/service/etc. This is centered on the provided geographic location.
