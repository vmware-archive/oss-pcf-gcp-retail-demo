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

import os
import json
from flask import (Flask, request, jsonify)
from flask_cors import CORS, cross_origin
import uuid
from random import randint
import base64
import urllib
import re
import operator
from collections import defaultdict
import inflect

DEBUG = True
MATCHER_APP = 'image-match'
N_ITEMS_IN_OFFER = 4
N_IMAGE_MATCHES = 20 # Must be > N_ITEMS_IN_OFFER, due to filtering
DEFAULT_TOP_TERM = 'item'

# FIXME: Make this dynamic
LOCATION_URL = 'https://goo.gl/maps/mDzTzVkWah82'

# This CORS section enables the Web UI component to use the /lastMessage endpoint
app = Flask(__name__)
cors = CORS(app, resources={r'/lastMessage': {'origins': '*'}})
port = int(os.getenv("PORT", 18080))

def logMsg(args):
    print "[Instance: %s] %s" % (str(os.getenv("CF_INSTANCE_INDEX", 0)), args)

hashtags = ['ootd', 'instafashion', 'vintage', 'fashionista', 'streetstyle',
  'stylish', 'lookbook']
def genHashtag():
  # TODO: incorporate post text into this
  return hashtags[randint(0, len(hashtags)-1)]

"""
  Consult the MATCHER_APP to get suggestions from inventory, and add these
  to the JSON msg as a new element, 'offer_items'.
"""
imgMatchUrl = None
def addOfferItems(msg):
  global imgMatchUrl
  offerItems = [] # Array of items from inventory which match the user's need
  if imgMatchUrl is None:
    vcapApp = json.loads(os.getenv('VCAP_APPLICATION'))
    thisHost = vcapApp['application_uris'][0]
    matcherHost = re.sub(r'^[^\.]+', MATCHER_APP, thisHost)
    imgMatcherUrl = 'http://' + matcherHost + '/query_image_url'
    logMsg('Image Matcher URL: %s' % imgMatcherUrl)
  makeOffer = ('make_offer' in msg and msg['make_offer'])
  topTerm = DEFAULT_TOP_TERM # This would be the term used in the tweet ("... some hot new TERM ...")
  if makeOffer and 'entities' in msg and 'media' in msg['entities']:
    # FIXME: Just taking the first image in the tweet
    imgUrl = msg['entities']['media'][0]['media_url']
    resp = urllib.urlopen(imgMatcherUrl + '/' + str(N_IMAGE_MATCHES) + '/' + base64.b64encode(imgUrl))
    match = json.loads(resp.read())
    termCounts = defaultdict(int)
    for item in match:
      # Elements: { 'sku': sku, 'price': price, 'desc': desc, 'url': url }
      # Ensure each one we append is relevant, per relevant_labels in JSON msg
      # Targeting N_ITEMS_IN_OFFER items
      termSet = set(msg['relevant_labels'])
      descSet = set(item['desc'].lower().split())
      overlapSet = termSet & descSet
      if len(overlapSet) > 0:
        for term in overlapSet:
          termCounts[term] += 1
        offerItems.append( { 'desc': item['desc'], 'url': item['url'] } )
      if len(offerItems) == N_ITEMS_IN_OFFER:
        break
    topTerm = sorted(termCounts.items(), key=operator.itemgetter(1))[-1][0]
  msg['top_term'] = topTerm
  msg['offer_items'] = offerItems

inflectEngine = inflect.engine()
def plural(word):
  return inflectEngine.plural(word)

# Save the most recent message here, for the "/lastMessage" endpoint to return
lastMessage = {}

# Determine whether to make an offer and, if so, add 'offer_text' item to JSON
"""
  Example offer (for Twitter):
    * pass in the PK to the offer
    * custom tailored #hashtag
    * text; e.g. "30% off at BohoChic with code #hashtag"
"""
@app.route('/', methods = ['POST', 'GET'])
def jsonHandler():
  global lastMessage
  obj = request.get_json(force=True)
  makeOffer = ('make_offer' in obj and obj['make_offer'])
  if makeOffer:
    addOfferItems(obj) # Sets 'top_term', which is referenced below
    offerId = str(uuid.uuid4()) # TODO: Store in persistence layer
    obj['offer_id'] = offerId
    userId = obj['user']['screen_name']
    obj['offer_text'] = 'Hey, @' + str(userId) + '. We have some hot new ' + plural(obj['top_term']) \
      + ' here: ' + LOCATION_URL + '  Use code #' + genHashtag() + ' for 30% off in store today!'
    obj['in_stock'] = True

  logMsg('Event: %s' % json.dumps(obj))
  lastMessage = obj
  return json.dumps(obj)

@app.route('/lastMessage')
def getLastMessage():
  return json.dumps(lastMessage)

@app.route('/status')
def test():
    return "STATUS_OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, threaded = not DEBUG, debug = DEBUG)

