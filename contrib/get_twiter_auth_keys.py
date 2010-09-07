#!/usr/bin/env python
#
# Copyright 2007 The Python-Twitter Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import sys
import madcow

sys.path.insert(0, os.path.join(os.path.dirname(madcow.__file__), 'include'))

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'

print '1. Go to http://dev.twitter.com/apps/new'
print '2. Fill out the form. Set the application type to "client"'
print '3. Enter in your Consumer key and Consumer secret here'
print

consumer_key    = raw_input('Consumer key: ')
consumer_secret = raw_input('Consumer secret: ')

if consumer_key is None or consumer_secret is None:
  print 'You need to edit this script and provide values for the'
  print 'consumer_key and also consumer_secret.'
  print ''
  print 'The values you need come from Twitter - you need to register'
  print 'as a developer your "application".  This is needed only until'
  print 'Twitter finishes the idea they have of a way to allow open-source'
  print 'based libraries to have a token that can be used to generate a'
  print 'one-time use key that will allow the library to make the request'
  print 'on your behalf.'
  print ''
  sys.exit(1)

signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
oauth_consumer             = oauth.Consumer(key=consumer_key, secret=consumer_secret)
oauth_client               = oauth.Client(oauth_consumer)

print 'Requesting temp token from Twitter'

resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET')

if resp['status'] != '200':
  print 'Invalid respond from Twitter requesting temp token: %s' % resp['status']
else:
  request_token = dict(parse_qsl(content))

  print ''
  print 'Please visit this Twitter page and retrieve the pincode to be used'
  print 'in the next step to obtaining an Authentication Token:'
  print ''
  print '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
  print ''

  pincode = raw_input('Pincode? ')

  token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
  token.set_verifier(pincode)

  print ''
  print 'Generating and signing request for an access token'
  print ''

  oauth_client  = oauth.Client(oauth_consumer, token)
  resp, content = oauth_client.request(ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % pincode)
  access_token  = dict(parse_qsl(content))

  if resp['status'] != '200':
    print 'The request for a Token did not succeed: %s' % resp['status']
    print access_token
  else:
    print 'Here are your auth keys for settings.py:'
    print
    print 'TWITTER_CONSUMER_KEY = %r' % consumer_key
    print 'TWITTER_CONSUMER_SECRET = %r' % consumer_secret
    print 'TWITTER_TOKEN_KEY = %r' % access_token['oauth_token']
    print 'TWITTER_TOKEN_SECRET = %r' % access_token['oauth_token_secret']
