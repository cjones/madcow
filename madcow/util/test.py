#!/usr/bin/env python

"""Test suite for madcow devel, put in module dir and run from CLI"""

from madcow import Request
from utils import Module
import sys
import re

any = re.compile(r'.+')
tests = {'learn': {'request': 'set karma cj_ 31337',
                   'result': "test: set cj_'s karma to 31337"},
         'wikiquotes': {'request': 'wq hitler', 'result': any},
         'hugs': {'request': 'hugs', 'result': any},
         'grufti': {'request': 'penis',
                    'result': re.compile(
                        r'hi\. :\)|8===D ~ ~|it that way\.|Joel\.  :\(|DOING'
                        r' DOING')},
         'google': {'request': 'google google',
                    'result': 'test: google = http://www.google.com/'},
         'lyrics': {'request': 'sing 1979',
                    'result': re.compile(r'Shakedown 1979')},
         'bbcnews': {'request': 'bbcnews',
                     'result': re.compile(r'http://news.bbc.co.uk/')},
         'weather': {'request': 'fc 94005',
                     'result': re.compile(r'Brisbane, California')},
         'seen': {'request': 'seen test',
                  'result': re.compile(
                      'test: test was last seen 0 seconds ago on test')},
         'memebot': {'request': 'http://google.com/',
                     'result': re.compile(r'First posted by j0no')},
         'woot': {'request': 'woot',
                  'result': re.compile(r'http://www.woot.com/')},
         'area': {'request': 'area 707',
             'result': 'test: 707: Santa Rosa, California'},
         'webtender': {'request': 'drinks fuzzy navel',
                       'result': re.compile(
                           r'test: Fuzzy Navel - 1/3 Peach schnapps')},
         'wikipedia': {'request': 'wiki wikipedia',
                       'result': re.compile(
                           r'Wikipedia - Wikipedia is a free, multilingual')},
         'chp': {'request': 'chp 101',
                 'result': re.compile(
                     r'(No incidents found|=>\s+[0-9:]+[AP]M)')},
         'factoids': [{'request': 'foo is bar',
                       'result': 'OK, test'},
                      {'request': 'foo?',
                       'result': re.compile(r'foo.*?(is|was).*?bar')},
                      {'request': 'forget foo',
                       'result': 'test: I forgot foo'}],
         'calc': {'request': 'calc 1+1', 'result': 'test: 1 + 1 = 2'},
         'war': {'request': 'terror',
                 'result': re.compile(u'Terror: \x1b\[[0-9;]*m\w+\x1b\[0m, DoomsDay: It is \d+ Minutes? to Midnight, BodyCount: [0-9, \u2013]*$'),
                 },
         'urban': {'request': 'urban penis',
                   'result': re.compile(
                       r'test: \[1/\d+\] Penis: The tool used to wean')},
         'dictionary': {'request': 'define penis',
                        'result': re.compile(r'the male organ of copulation')},
         'conservapedia': {'request': 'cp penis',
                           'result': re.compile(
                               r'Human reproduction - Human reproduction')},
         'slut': {'request': 'slutcheck penis',
                  'result': re.compile(r'penis is [0-9.]+% slutty')},
         'bash': [{'request': 'bash cj_', 'result': re.compile(r'cj', re.I)},
                  {'request': 'qdb cj_', 'result': re.compile(r'cj', re.I)},
                  {'request': 'limerick', 'result': any}],
         'nslookup': {'request': 'nslookup localhost',
                      'result': 'test: 127.0.0.1'},
         'bible': {'request': 'bible john 3:16',
                   'result': re.compile('For God so loved the world, that he gave')},
         'yourmom': {'request': 'yourmom', 'result': any},
         'roll': {'request': 'roll 2d20',
                  'result': re.compile(r'test rolls \d+, needs \d+, test')},
         'livejournal': {'request': 'lj cj_',
                         'result': re.compile(r'THIS IS MY UPDATE')},
         'summon': {'request': 'summon asdf',
                    'result': re.compile(r"I don't know the email for asdf")},
         'karma': {'request': 'karma cj_',
                   'result': re.compile(r"test: cj_'s karma is \d+")},
         'babel': {'request': 'translate from english to spanish: your mom',
                 'result': u'test: tu mam\xe1'},
         'movie': {'request': 'rate bone collector',
                   'result': 'test: IMDB: 6.3/10, RT: 27%'},
         'stockquote': {'request': 'quote goog',
                        'result': re.compile(r'Google Inc\.')},
         'artfart': {'request': 'artfart',
                     'result': re.compile(r'>>> .+ <<<')},
         'alias': [{'request': 'alias add g quote goog',
                    'result': 'alias added'},
                   {'request': 'alias del 1', 'result': 'deleted alias: g'}],
         'care': {'request': 'care 50',
                  'result': (
                      'CARE-O-METER: |....................o..................'
                      '.|')},
         'clock': {'request': 'time in budapest',
                   'result': re.compile(
                       r'test:\s+\d+:\d+[ap]m\s+\w+\s+\(CEST\)\s+-\s+Time in B'
                       r'udapest, Hungary')},
         'obama': {'request': 'obama',
                   'result': re.compile(r'Bush has been gone.*?\d')},
         'election2008': {'request': 'ev',
                          'result': re.compile(
                              r'^test: Projected Senate Seats 2010:.*?Democra'
                              r'ts.*?: \d+, .*?Republicans.*?: \d+')},
         'spellcheck': {'request': 'spell gerbage',
                        'result': 'test: garbage'},
         'figlet': {'request': 'figlet hi', 'result': any},
         'fmylife': {'request': 'fml', 'result': any},
         'joke': {'request': 'joke', 'result': any},
         'megahal': {'request': 'mh hi',
                     'result': 'I am utterly speechless!'},
         'traffic': {'request': 'traffic from sunnyvale to brisbane',
                     'result': re.compile(r'test: \d+ mins\.')},
         'wardb': {'request': 'wardb rock',
                   'result': re.compile(r'.*?Azure-rock.*?: No bonuses')},
         'delicious': None,
         'jinx': None,
         'steam': None,
         'cnn': {'request': 'cnn', 'result': re.compile(r'http://rss\.cnn\.com')},
         'noaa': {'request': 'noaa 94005', 'result': re.compile(r'Visibility')},
         'texts': {'request': 'txt', 'result': re.compile(r'\(\d+')},
         'trek': {'request': 'trek', 'result': re.compile(r'test: \x1b\[[0-9;]+mFAIL\x1b\[0m: .+ \x1b\[[0-9;]+mFIX\x1b\[0m: .+$')},

         'yelp': {'request': 'yelp madhouse @94005', 'result': re.compile(r'test: Madhouse Coffee')},
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
        failed_list = []
        for mod_name, mod_data in self.madcow.modules.modules.iteritems():
            obj = mod_data['obj']
            #for mod_name, obj in self.madcow.modules:
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
                failed_list.append(mod_name)
            results[mod_name] = passed
        tested = len(results)
        passed = len([m for m, r in results.items() if r])
        return u'results: %s / %s passed\nfailed: %s' % (passed, tested, ', '.join(failed_list))

