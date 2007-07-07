#!/usr/bin/env python

# Lots of really awful your mom jokes

import sys
import re
import random

# class for this module
class match(object):
  def __init__(self, config=None, ns='default', dir=None):
    self.enabled = True       # True/False - enabled?
    self.pattern = re.compile('^your mom$') # regular expression that needs to be matched
    self.requireAddressing = False      # True/False - require addressing?
    self.thread = False       # True/False - should bot spawn thread?
    self.wrap = False       # True/False - wrap output?
    
    filename = dir + '/momjokes.txt'
    
    try:
      f = file(filename)
      self.jokes = map(str.strip, f.readlines())
      f.close()
    except:
      self.enabled = False
  
  def response(self, *args, **kwargs):
    if self.enabled is False: return
    return random.choice(self.jokes)
  