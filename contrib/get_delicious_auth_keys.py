#!/usr/bin/env python

import os
import sys
sys.path.insert(0, '/home/cjones/madcow')
sys.dont_write_bytecode = True
import madcow

sys.path.insert(0, os.path.join(os.path.dirname(madcow.__file__), 'include'))

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth

REQUEST_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth/v2/request_auth'
ACCESS_TOKEN_URL  = 'https://api.login.yahoo.com/oauth/v2/get_token'

print '1. Go to https://developer.apps.yahoo.com/projects'
print '2. Click "New Project" button'
print '3. Select the middle option "Create desktop and Web apps that use Yahoo! open authentication (OAuth) APIs"'
print '4. Fill out the form, with "Kind of Application" being client/desktop'
print '5. For access scopes, select "This app requires access to private user data."'
print '6. Change access type for Delicious to read-write'

consumer_key    = raw_input('API Key: ')
consumer_secret = raw_input('Shared Secret: ')

oauth_consumer             = oauth.Consumer(key=consumer_key, secret=consumer_secret)
oauth_client               = oauth.Client(oauth_consumer)

print 'Requesting temp token from Yahoo'

resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET', callback='oob')

if resp['status'] != '200':
  print 'Invalid respond from Yahoo requesting temp token: %s' % resp['status']
else:
  request_token = dict(parse_qsl(content))

  print ''
  print 'Please visit this Yahoo page and retrieve the pincode to be used'
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
    print 'DELICIOUS_CONSUMER_KEY = %r' % consumer_key
    print 'DELICIOUS_CONSUMER_SECRET = %r' % consumer_secret
    print 'DELICIOUS_TOKEN_KEY = %r' % access_token['oauth_token']
    print 'DELICIOUS_TOKEN_SECRET = %r' % access_token['oauth_token_secret']
