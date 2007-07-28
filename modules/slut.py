#!/usr/bin/env python
# 
#  slut.py
#  madcow-1.31
#  
#  Created by Bryan Burns on 2007-06-20.
# 

"""
Slutcheck - Uses google "safesearch" to determine how "slutty" a word or phrase is.  (To get an accurate
slut rating for a phrase it should be quoted.)

Uses the ratio of hits doing an unsafe search to the number of hits doing a safe search to determine the score.
If a safe search returns 0 results, and unsafe returns, say, 100, the phrase is 100% slutty.  If the number of
results for both are equal, the phrase is 0% slutty.
"""
import urllib2
import sys
import re

class WordFiltered(Exception):
  """Indicates a word has been filtered by google safe search"""
  def __init__(self, word):
    self.word = word

  def __str__(self):
    return repr(self.word)

matchpattern = "Results .* of about <b>([\d,]+)</b> for"
filterpattern = 'The word <b>"(\w+)"</b> has been filtered from the search'
searchURL = "http://www.google.com/search?q="

def cleanurl(url):
  return url.replace(" ", "+")

def slutrating(phrase):
  phrase = cleanurl(phrase)
  
  opener = urllib2.build_opener()
  opener.addheaders = [("User-agent", "Mozilla/5.0 - slutbot")]
  
  for i in xrange(5): # Try up to 5 times to get a good result
    try:
      data = opener.open(searchURL + phrase + "&safe=off").read()
      unsafecount = int(re.search(matchpattern, data).groups()[0].replace(",",""))
    except:
      unsafecount = 0
    
    try:
      data = opener.open(searchURL + phrase + "&safe=active").read()
      try:
        filteredword = re.search(filterpattern, data).groups()[0]
        raise WordFiltered, filteredword
      except (AttributeError, IndexError):
        pass # no filtered word, so continue
      safecount = int(re.search(matchpattern, data).groups()[0].replace(",",""))
    except (AttributeError, IndexError):
      safecount = 0
    
    if unsafecount == 0:
      if safecount > 0:
        continue # shouldn't really be possible to have safe w/o unsafe
      else:
        return 0
    
    value = float(unsafecount-safecount)/float(unsafecount)
    if value > 0:
      return value
  
  return None

# class for this module
class MatchObject(object):
  def __init__(self, config=None, ns='madcow', dir=None):
    self.enabled = True
    self.pattern = re.compile('^\s*slutcheck\s+(.+)')
    self.requireAddressing = True
    self.thread = True
    self.wrap = False
    self.help = "slutcheck <phrase> - see how slutty the phrase is"
  
  # function to generate a response
  def response(self, **kwargs):
    nick = kwargs['nick']
    args = kwargs['args']
    try:
      query = " ".join(args)
      rating = slutrating(query)
      return "%s is %.2f%% slutty." % (query, rating*100)
    except TypeError:
      return "%s: Sorry, google isn't being cooperative.." % nick
    except WordFiltered, wf:
      return "%s: Hmm, google is filtering the word '%s'.." % (nick, wf.word)
    except Exception, e:
      print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
      return '%s: I failed to perform that lookup' % nick
  

# this is just here so we can test the module from the commandline
def main(argv = None):
  if argv is None: argv = sys.argv[1:]
  obj = MatchObject()
  print obj.response(nick='testUser', args=argv)
  
  return 0

if __name__ == '__main__': sys.exit(main())
