#!/usr/bin/env python

"""Test suite for madcow devel, put in module dir and run from CLI"""

from madcow import Request
from include.utils import Module
import sys
import re

any = re.compile(r'.+')
tests = {
        u'learn': {
            u'request': u'set karma cj_ 31337',
            u'result': u"test: set cj_'s karma to 31337",
            },
        u'wikiquotes': {
            u'request': u'wq hitler',
            u'result': any,
            },
        u'hugs': {
            u'request': u'hugs',
            u'result': any,
            },
        u'grufti': {
            u'request': u'penis',
            u'result': re.compile(
                r'hi\. :\)|8===D ~ ~|it that way\.|Joel\.  :\('),
            },
        u'google': {
            u'request': u'google google',
            u'result': u'test: google = http://www.google.com/',
            },
        u'lyrics': {
            u'request': u'sing 1979',
            u'result': re.compile(r'Shakedown 1979'),
            },
        u'bbcnews': {
            u'request': u'bbcnews',
            u'result': re.compile(r'http://news.bbc.co.uk/'),
            },
        u'weather': {
            u'request': u'fc 94005',
            u'result': re.compile(r'Brisbane, California'),
            },
        u'seen': {
            u'request': u'seen test',
            u'result': re.compile(
                u'test: test was last seen 0 seconds ago on test'),
            },
        u'memebot': {
            u'request': u'http://google.com/',
            u'result': re.compile(r'first posted by j0no'),
            },
        u'woot': {
            u'request': u'woot',
            u'result': re.compile(r'http://www.woot.com/'),
            },
        u'area': {
            u'request': u'area 707',
            u'result': u'test: 707 = Santa Rosa, California',
            },
        u'webtender': {
            u'request': u'drinks fuzzy navel',
            u'result': re.compile(r'test: Fuzzy Navel - 1/3 Peach schnapps'),
            },
        u'wikipedia': {
                u'request': u'wiki wikipedia',
                u'result': re.compile(
                    r'Wikipedia - Wikipedia is a free, multilingual'),
                },
        u'chp': {
                u'request': u'chp 101',
                u'result': re.compile(r'(No incidents found|=>\s+[0-9:]+[AP]M)'),
                },
        u'factoids': [
                {
                    u'request': u'foo is bar',
                    u'result': u'OK, test',
                    },
                {
                    u'request': u'foo?',
                    u'result': re.compile(r'foo.*?(is|was).*?bar'),
                    },
                {
                    u'request': u'forget foo',
                    u'result': u'test: I forgot foo',
                    },
                ],
        u'calc': {
                u'request': u'calc 1+1',
                u'result': u'test: 1 + 1 = 2',
                },
        u'war': {
                u'request': u'terror',
                u'result': re.compile(
                    u'Terror: \x1b\[1;33m.*?\x1b\[0m, DoomsDay: It is \d+ Minu'
                    u'tes to Midnight, IranWar: .*?, IraqWar: .*?, BodyCount'),
                },
        u'urban': {
                u'request': u'urban penis',
                u'result': re.compile(r'test: \[1/20\] The tool used to wean'),
                },
        u'dictionary': {
                u'request': u'define penis',
                u'result': re.compile(r'a male erectile organ'),
                },
        u'conservapedia': {
                u'request': u'cp penis',
                u'result': re.compile(
                    r'Human reproduction - Human reproduction'),
                },
        u'slut': {
                u'request': u'slutcheck penis',
                u'result': re.compile(r'penis is [0-9.]+% slutty'),
                },
        u'bash': [
                {
                    u'request': u'bash cj_',
                    u'result': re.compile(r'cj_'),
                    },
                {
                    u'request': u'qdb cj_',
                    u'result': re.compile(r'cj_'),
                    },
                {
                    u'request': u'limerick',
                    u'result': any,
                    },
                ],
        u'nslookup': {
                u'request': u'nslookup localhost',
                u'result': u'test: 127.0.0.1',
                },
        u'bible': {
                u'request': u'bible john 3:16',
                u'result': re.compile(
                    u'"For God so loved the world that he gave'),
                },
        u'yourmom': {
                u'request': u'yourmom',
                u'result': any,
                },
        u'roll': {
                u'request': u'roll 2d20',
                u'result': re.compile(r'test rolls \d+, needs \d+, test'),
                },
        u'livejournal': {
                u'request': u'lj cj_',
                u'result': re.compile(
                    r'HI PEOPLE WHO HAVE ME FRIENDED FOR SOME REASON'),
                },
        u'summon': {
                u'request': u'summon asdf',
                u'result': re.compile(r"I don't know the email for asdf"),
                },
        u'karma': {
                u'request': u'karma cj_',
                u'result': re.compile(r"test: cj_'s karma is \d+"),
                },
        u'babel': {
                u'request': u'translate from english to spanish: your mom',
                u'result': u'test: tu madre',
                },
        u'movie': {
                u'request': u'rate bone collector',
                u'result': (
                    u'test: IMDB: 6.3/10, Freshness: 28%, Meta - Critics: 45/1'
                    u'00, Users: 5.0/10'),
                },
        u'stockquote': {
                u'request': u'quote goog',
                u'result': re.compile(r'Google Inc\.  \(GOOG\)'),
                },
        u'artfart': {
                u'request': u'artfart',
                u'result': re.compile(r'>>> .+ <<<'),
                },

        u'delicious': None,
    u'jinx': None,
}

retype = type(re.compile(u''))

class Main(Module):
    pattern = re.compile(r'^\s*runtest(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = u'runtest - run test suite'

    def __init__(self, madcow=None):
        self.madcow = madcow
        if madcow.config.main.module != u'cli':
            self.enabled = False

    def response(self, nick, args, kwargs):
        testmod = args[0]
        results = {}
        for mod_name, obj in self.madcow.modules:
            if testmod is not None and mod_name != testmod:
                continue
            try:
                test = tests[mod_name]
            except:
                continue
            if not test:
                continue
            if isinstance(test, dict):
                test = [test]
            passed = True
            sys.stderr.write(u'testing %s ... ' % mod_name)
            for t in test:
                try:
                    response = u''
                    req = Request(message=t[u'request'])
                    req.nick = u'test'
                    req.channel = u'test'
                    req.private = True
                    req.sendto = u'test'
                    req.addressed = True
                    req.colorize = False
                    req.correction = True
                    try:
                        args = obj.pattern.search(req.message).groups()
                    except:
                        print u"\n* args didn't match"
                        passed = False
                        break
                    kwargs = {u'req': req}
                    kwargs.update(req.__dict__)
                    response = obj.response(req.nick, args, kwargs)
                    if isinstance(t[u'result'], str):
                        if response != t[u'result']:
                            passed = False
                            print u"\n* string object didn't match"
                            break
                    elif isinstance(t[u'result'], retype):
                        if t[u'result'].search(response) is None:
                            passed = False
                            print u"\n* regex didn't match"
                            break
                except Exception, error:
                    print u"\n* exception: %s" % error
                    passed = False
            if passed:
                sys.stderr.write(u'ok\r\n')
            else:
                sys.stderr.write(u'fail [%s]\r\n' % repr(response))
            results[mod_name] = passed
        tested = len(results)
        passed = len([m for m, r in results.items() if r])
        return u'results: %s / %s passed' % (passed, tested)

