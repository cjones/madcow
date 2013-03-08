
REQUIREMENTS
============

* python 2.7

* Various optional modules have their own requirements, though care has
  been taken to use only Python when at all possible. These requirements
  are noted in the config file where appropriate and disabled by
  default.

* If you wish to use the SILC protocol, you need pysilc-0.5 and
  silc-toolkit-1.1.8. I have not tested any newer ones, and older ones
  stopped working. I highly discourage using SILC. SSL support in IRC is
  now common, and it works better (which is saying a LOT). I may drop
  support for SILC at some point in the future.


MADCOW AS A SHARED LIBRARY
==========================

This type of install uses distutils like any other Python library to
install the core bot, as well as installs a script in the prefix bin dir
that will launch it. Data files are stored in ~/.madcow by default. You
may change this with the -b option. Example usage:

    # install
    python setup.py build
    sudo python setup.py install

    # running with a non-standard datadir
    madcow -b /var/lib/madcow


MADCOW AS A STANDALONE BOT
==========================

Alternatively, you may run madcow from the source directory and skip
installation entirely. A script suited to this purpose is included in
the project root:

    ./run-standalone-madcow -h  # show help

By default it will look for the runtime files in the same directory, and
store its data files in "./data". Both of these may be changed: run the
script with -h for usage help.


CONFIGURATION
=============

The first time you run madcow, it will create a data directory if
necessary, place a default config file there (settings.py, like Django),
and exit, encouraging you to edit this file. In a UNIX environment, it
will try to launch your editor on it if $EDTIOR or $VISUAL are set (run
with -n to suppress this). You should take this opportunity to carefully
go over all of the settings and set them to appropriate values. Most of
the documentation is in comments in the settings file.

The second time you run the bot, it will launch as expected. I abstain
from the venerable tradition of putting DIE statements at random places
in a massive config file for you to hunt down. If you fail to edit the
config, the bot will launch as a fairly barebones CLI-only response bot.
Incidentally, this is a useful mode to test if its behavior is
appropriate before configuring it to join an IRC channel. (For module
development, madcow can be configured to use an IPython shell for
interaction.)

In any case, you probably want to set the protocol to IRC and fill out
the server/channel info at the bare minimum.


BASIC USAGE
===========

In IRC, message the bot with 'help' to see a list of commands. To
trigger her publicly, most commands require that you address the bot by
its given nick, for example:

    <cj_> madcow: wiki dinosaurs
    <madcow> Dinosaur - Dinosaurs were the dominant vertebrate
             animals of terrestrial ecosystems for over 160 million
             years, from the late Triassic period to the end of the
             Cretaceous period, when most of them became extinct in
             the CretaceousTertiary extinction event.


This doesn't apply to CLI mode, which behaves as if the entire session is
a private query window. Madcow can also be configured to accept aliases
(such as !) for triggers, or to only respond in private message, or to
ignore certain patterns in chat regardless of how the rest of it is
configured, along other things. Please see the settings.py file for
these options.


SERIOUS DISCLAIMER DO READ ME
=============================

*WARNING! WARNING! WARNING! WARNING! WARNING! WARNING!*

You will notice that fully half of the optional modules are disabled by
default, for no apparent reason. This is because many can and do produce
wildly offensive content that would not be appropriate in many contexts,
such as a work IRC server -- especially if you are in the U.S. This is
often contingent on what the bot is queried with, of course, but some
are more "dangerous" than others in this regard, such as urban
dictionary.

Others are just plain spammy, which goes over great in IRC channels with
a certain type of culture, while being despised with surprising ferocity
in yet others. It's up to you to vet its behavior such that it fits in
with existing chat culture.

Another reason these are disabled is that without further configuration
of flood thresholds, they are liable to cause the bot to be booted
automatically. I run it on a private server and exempt it from
throttling, but you will have to be mindful of this on most public
networks, especially large ones that have had to weather DDoS attacks
over the years and often have very strict flood policy as a result. Some
networks disallow bots entirely, and will ban you for violations. Do read
the rules/motd if it's not your server!

To put it another way, I am not responsible for lost jobs, lost friends,
bannination, k-lines, or civil lawsuits that result from madcow
misbehaving. Especially if you didn't test it, but even if you do.
Responsibility fully disclaimed.


PRIVACY
=======

In addition to permanent ignore patterns in config, you may force madcow
to ignore a line of chat by placing NOBOT anywhere in the text. This is
useful if you have URL logging enabled and wish to post a link that does
not get saved there, like naked pics. There are other options in
settings.py for more permanent solutions to privacy concerns, but if
other chat participants routinely complain about some functionality you
have enabled, my suggestion is to turn it off.


AUTO-OPS
========

In settings.py, set owner name to your IRC nick. Message bot with 'admin
register <password>'. This will register you as an admin. Other users
may now register, and you can give them auto-op flag with /msg madcow
admin chflag <user> +o. You can also set the default flags to give any
user that registers auto-ops if so desired.

If you wish to batch-add users for auto-op access without them
registering, edit db/passwd and add a line for each user:

    nick:*:o

They will not be able to login in this case, as no password is set, but
this feature of madcow is pretty rudimentary, and there isn't actually
anything else you can do after logging in. In my opinion, you should use
ChanServ/NickServ for these purposes, it is a vastly superior way of
managing channel permissions than any IRC bot, which doesn't have the
permissions to effectively manage a channel the way services do (even
when opered, depending on the ircd).


TWITTER
=======

Set up a twitter account and follow the people you want to see updates
from. Then run:

    ./contrib/get_twiter_auth_keys.py

and follow the directions. At the end of the process you should have 4
settings you can copy-paste into your settings.py. Be sure to delete the
settings already there, or paste at the bottom.

This module currently does not allow outgoing tweets, as the API is very
strict. Just polling it often enough to produce updates keeps it just
barely on the acceptable usage side of the line. Any further API
requests would cause it to get a temporary ban, which last anywhere from
20 minutes to several days before expiring. Madcow's twitter module
uses the API method provided that informs of how close to violating this
the policy it is, and adapts as needed to avoid going over it.


CONTACT
=======

You may reach me by e-mail at cjones at gmail.com, but a better way to
report bugs is at the github project page which has a bug tracker I
occasionally look at. It is here:  http://github.com/cjones/madcow
