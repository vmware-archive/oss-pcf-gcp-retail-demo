#!/usr/bin/env python

# 
# Copyright (c) 2017-Present Pivotal Software, Inc. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

DEBUG = False # If True, the Flask app is not multi-threaded
SOURCE_NAME = 'twitter'
OUR_SCREEN_NAME='bohochicsf' # For *our* Twitter account
POLLING_INTERVAL_SEC = 15
UPDATE_FOLLOWERS_INTERVAL_SEC = 60

from datetime import datetime
import os, sys, re, time, urllib2, json
from flask import (Flask, request, jsonify)
import tweepy
import cStringIO
import threading
import time
import urllib
import tempfile

import uuid # FIXME: this UUID should be persisted for retrieval at PoS terminal in store

"""
Setup:
(1) Deploy the SCDF stream
(2) Use `cf apps` to get the URI of the HTTP Source app
(3) Create a service named "http-hub" using this URI value:
    cf cups http-hub -p '{"uri": "THIS_URI_VALUE"}'
(4) `cf push --no-start` (this app)
(5) Bind to http-hub: `cf bs `
"""

# This is the name of the user-provided service in (3)
SERVICE_NAME = 'http-hub'

# Fetch the URI of the HTTP Source from VCAP_SERVICES
uri = None
USER_PROVIDED = 'user-provided'
vcap = json.loads(os.getenv('VCAP_SERVICES', '{}'))
if USER_PROVIDED in vcap:
  for cred in vcap[USER_PROVIDED]:
    if cred['name'] == SERVICE_NAME:
      uri = cred['credentials']['uri']
if uri is None:
  err_str = 'This app must be bound to a user-provided service named "%s"' % SERVICE_NAME
  raise BaseException(err_str)
print 'URI: %s' % uri

app = Flask(__name__)
port = int(os.getenv("PORT", 18080))

def logMsg(args):
    print "[Instance: %s] %s" % (str(os.getenv("CF_INSTANCE_INDEX", 0)), args)

def sendJson(msg):
  req = urllib2.Request(uri)
  req.add_header('Content-Type', 'application/json')
  response = urllib2.urlopen(req, json.dumps(msg))
  return "OK"

# Set up Twitter auth, get API instance
conKey = os.getenv('CONSUMER_KEY')
if conKey is None:
  raise BaseException('Environment not properly initialized for Twitter API')
auth = tweepy.OAuthHandler(os.getenv('CONSUMER_KEY'), os.getenv('CONSUMER_SECRET'))
auth.set_access_token(os.getenv('ACCESS_KEY'), os.getenv('ACCESS_SECRET'))
api = tweepy.API(auth_handler=auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

def uidFromScreenName(screenName):
  user = api.get_user(screen_name=screenName)
  return str(user.id)

def getTimestamp():
  d1 = datetime.now()
  return d1.strftime('[%m/%d/%y %I:%M:%S]')

# Set containing screen names of *our* followers
followerSet = set()
lastFollowerUpdateT = time.time()
def updateFollowerSet():
  global followerSet
  global lastFollowerUpdateT
  print 'Updating followerSet'
  for user in tweepy.Cursor(api.followers, screen_name=OUR_SCREEN_NAME).items():
    if user.screen_name not in followerSet:
      print 'Adding "%s"' % user.screen_name
      followerSet.add(user.screen_name)
  lastFollowerUpdateT = time.time()
  # Call ourself every so often
  threading.Timer(UPDATE_FOLLOWERS_INTERVAL_SEC, updateFollowerSet).start()

# Maps screenName => lastTweetId
lastTweetId = {}

def getStatusForUser(screenName):
  if screenName in lastTweetId:
    rv = api.user_timeline(screen_name=screenName, since_id=lastTweetId[screenName])
  else:
    rv = api.user_timeline(screen_name=screenName)
  return rv

# Use with threaded version
stopPolling = False
lastTimelineUpdateT = time.time()
def timelinePoller(lastTweetId):
  global lastTimelineUpdateT
  while not stopPolling:
    for screenName in followerSet:
      print 'Polling "%s" at %s' % (screenName, getTimestamp())
      sendIt = False
      for status in getStatusForUser(screenName):
        if screenName in lastTweetId:
          if status.id > lastTweetId[screenName]:
            lastTweetId[screenName] = status.id
            sendIt = True
          else:
            sendIt = False
        else:
          lastTweetId[screenName] = status.id
        if sendIt:
          data = status._json # The _json field of Status is a dictionary
          print '%s tweeted: %s' % (screenName, json.dumps(data))
          d1 = datetime.now()
          data['date_time'] = d1.strftime('%m/%d/%y %I:%M:%S')
          data['source'] = SOURCE_NAME
          sendJson(data)
      print 'Max tweet ID for "%s": %s' % (screenName, str(lastTweetId[screenName]))
    lastTimelineUpdateT = time.time()
    time.sleep(POLLING_INTERVAL_SEC)

# Tweet an offer, tagging the user
# The API won't allow duplicate status updates so, if you do that, go into the Web
# view of the sender's Twitter account and delete the previous tweet.
"""
# Here's how to handle posting > 1 image

# https://github.com/tweepy/tweepy/issues/724

images = ('image1.png', 'image2.png')
media_ids = [api.media_upload(i).media_id_string for i in images]
api.update_status(status=msg, media_ids=media_ids)

"""
@app.route('/', methods = ['POST', 'GET'])
def sendOffer():
  obj = request.get_json(force=True)
  offerId = obj['offer_id']
  offerText = obj['offer_text']
  urlList = obj['url_list']
  statusId = obj['status_id']
  print 'urlList: ', urlList
  print 'Offer: [%s] %s' % (offerId, offerText)
  # Download images
  tmpDir = tempfile.gettempdir()
  imgList = []
  for imgUrl in urlList:
    fileName = imgUrl.split('/')[-1]
    tmpFile = tmpDir + '/' + fileName
    print 'Downloading image %s now ...' % imgUrl
    urllib.urlretrieve(imgUrl, tmpFile)
    imgList.append(tmpFile)
  # Tweet the offer with multiple images attached
  media_ids = [api.media_upload(img).media_id_string for img in imgList]
  status = api.update_status(status=offerText, media_ids=media_ids, in_reply_to_status_id=statusId)
  # Delete those images from tmpDir
  for imgFile in imgList:
    os.remove(imgFile)
  return jsonify(status._json)

"""
Add the following to the manifest for this to determine health:
  health-check-type: http
  health-check-http-endpoint: /health

There are a couple of health metrics to monitor here:
  1. updateFollowerSet
  2. timelinePoller
Each of these should have been run within about the specified sleep times
"""
nHealthCalls = 0
@app.route('/health')
def health():
  global nHealthCalls
  nHealthCalls += 1
  httpCode = 200
  tNow = time.time()
  # Add a second to the delta T value
  if (tNow - lastTimelineUpdateT > POLLING_INTERVAL_SEC + 1.0) or (tNow - lastFollowerUpdateT > UPDATE_FOLLOWERS_INTERVAL_SEC + 1.0):
    httpCode = 503
  print '/health returning HTTP %d (called %d times)' % (httpCode, nHealthCalls)
  return "STATUS_OK", httpCode

if __name__ == '__main__':
  # Set up Twitter handler
  updateFollowerSet()
  listener = threading.Thread(target=timelinePoller, args=[lastTweetId])
  listener.setDaemon(True)
  listener.start()
  # Start REST app
  app.run(host='0.0.0.0', port=port, threaded = not DEBUG, debug = DEBUG)
  stopPolling = True
  listener.join(POLLING_INTERVAL_SEC)

