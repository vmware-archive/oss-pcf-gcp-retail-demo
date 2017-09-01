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

from __future__ import division
import os, re, json, base64
import urllib2, random
from flask import (Flask, request, jsonify, Response)

from google.cloud import language
from google.cloud import vision
import redis, pickle
from collections import defaultdict

from pcfgcp import PcfGcp

DEBUG = False
LABEL_FRACTION = 0.3  # Min. fraction of image labels in labelSet to trigger an offer TODO: Make tunable
IMAGE_RESIZER_APP = 'image-resizing-service'
app = Flask(__name__)
port = int(os.getenv("PORT", 18080))
pg = PcfGcp()

# Redis setup
if 'VCAP_SERVICES' in os.environ:
    services = json.loads(os.getenv('VCAP_SERVICES'))
    redis_env = services['p-redis'][0]['credentials']
else:
    redis_env = dict(host='localhost', port=6379, password='')
redis_env['port'] = int(redis_env['port'])

# Connect to redis
try:
    redisConn = redis.StrictRedis(**redis_env)
    redisConn.info()
except redis.ConnectionError:
    redisConn = None
redisNS = __file__.split('/')[-1]  # Namespace for Redis keys

# Set of top 250 terms found in the item descriptions, generated by running
# ./scripts/generate_product_word_list.py https://storage.googleapis.com/retail-image/toc.txt
# These are all lower case
MAX_TERMS = 250
termSet = set()
termSetRedisKey = redisNS + ':termSet'
tmpTermSet = redisConn.get(termSetRedisKey)
if tmpTermSet is not None:
    termSet = pickle.loads(tmpTermSet)
print 'termSet: %s' % json.dumps(sorted(termSet))

# Set of labels corresponding with items within our retailer's inventory
# This set was created using ./scripts/generate_labels_for_images.py
# These are all lower case, so use lower() when testing against this set
labelSet = set()
labelSetRedisKey = redisNS + ':labelSet'
tmpLabelSet = redisConn.get(labelSetRedisKey)
if tmpLabelSet is not None:
    labelSet = pickle.loads(tmpLabelSet)
print 'labelSet: %s' % json.dumps(sorted(labelSet))


def logMsg(args):
    print "[Instance: %s] %s" % (str(os.getenv("CF_INSTANCE_INDEX", 0)), args)


"""Returns a URL which will run the image through the image resizing app to ensure
it fits into the bounds suggested by the GCP Vision API, for label detection.

The return value here should be passed into the Vision API as the `source_uri`
(see below)

Requires this app to be bound to a user provided service pointing to the resizing
app (https://github.com/cf-platform-eng/image-resizing-service)
"""
imgSize = 640
imgResizerUrl = None


def getResizedImageUrl(origUrl):
    global imgResizerUrl
    if imgResizerUrl is None:
        vcapApp = json.loads(os.getenv('VCAP_APPLICATION'))
        thisHost = vcapApp['application_uris'][0]
        imgHost = re.sub(r'^[^\.]+', IMAGE_RESIZER_APP, thisHost)
        imgResizerUrl = 'http://' + imgHost + '/'
    # Format => http://localhost:18080/?size=256&urlBase64=aHR0cDoL3...QmlcGc=
    rv = '{}?size={}&urlBase64={}'.format(imgResizerUrl, imgSize, base64.b64encode(origUrl))
    logMsg('Resize image URL: %s' % rv)
    return rv


"""Detects labels in the file located in Google Cloud Storage or on the Web.
  Ref. https://googlecloudplatform.github.io/google-cloud-python/stable/vision-usage.html

  Example:
  labels = image.detect_labels(limit=3)
  labels[0].description # => 'automobile'
  labels[0].score => 0.9863683

  Returns: List of label values
"""
def detectLabelsUri(uri):
    client = pg.getVision()
    image = client.image(source_uri=getResizedImageUrl(uri))
    labels = []
    for label in image.detect_labels():
        labels.append(label.description.lower())  # lower() to match labelSet
    return labels


def getMessageText(msg):
    return msg['text']  # For Twitter


# FIXME: Factor out all Twitter specific parts into the "twitter" module
@app.route('/', methods=['POST', 'GET'])
def jsonHandler():
    obj = request.get_json(force=True)
    makeOffer = False
    msgText = getMessageText(obj)

    # Analyze document using GCP ML Language API
    # Any sentiment value > 0 triggers offer
    lang = pg.getLanguage()
    doc = lang.document_from_text(msgText)
    annotations = doc.annotate_text(include_sentiment=True, include_syntax=False, include_entities=False)
    obj['sentiment'] = {
        'score': annotations.sentiment.score,
        'magnitude': annotations.sentiment.magnitude
    }
    if annotations.sentiment.score > 0.0:
        makeOffer = True

    # Here, if the message contains references to images, check the image labels;
    # if there are no images, then analyze the message itself against the set of
    # terms relevent to our inventory.
    relevantLabels = []
    if makeOffer and 'entities' in obj and 'media' in obj['entities']:
        # Handle any image references using GCP ML Vision API
        labelScore = 0
        numLabels = 0
        for mediaItem in obj['entities']['media']:
            imgUrl = mediaItem['media_url']
            logMsg('Image URL: %s' % imgUrl)
            labels = detectLabelsUri(imgUrl)
            numLabels += len(labels)
            for label in labels:
                if label in labelSet:
                    relevantLabels.append(label)
                    labelScore += 1
            # Add this label's array as a new attribute
            mediaItem['vision_labels'] = labels
        # Combine sentiment based offer decision with image based one
        makeOffer &= (labelScore / numLabels >= LABEL_FRACTION)
    else:
        # Analyze terms in text to see if they occur in item termSet
        nHits = 0
        for word in re.split(r'[^\w_]+', msgText.lower()):
            if len(word) > 2 and word in termSet:
                nHits += 1
        makeOffer &= (nHits > 0)
        # 27 April 2017: for now, images are required for us to make an offer
        makeOffer = False

    # TODO: More sophisticated analysis of syntax to trigger offer
    # Try a GloVe model of "need", "desire", etc. (https://github.com/maciejkula/glove-python)
    obj['relevant_labels'] = relevantLabels
    obj['make_offer'] = makeOffer
    logMsg(json.dumps(obj, sort_keys=True, indent=2))
    return json.dumps(obj)


@app.route('/status')
def test():
    return "STATUS_OK"


imageTocUrl = os.getenv('IMAGE_TOC_URL')
if imageTocUrl is None:
    raise Exception('Environment variable "IMAGE_TOC_URL" must be set to the URL of a listing of image files')
imageBaseUrl = '/'.join(imageTocUrl.split('/')[:-1])
print 'imageTocUrl: %s, imageBaseUrl: %s' % (imageTocUrl, imageBaseUrl)

# Generate image labels and append them to labelSet
@app.route('/genLabelSet/<int:n_images>')
def genLabelSet(n_images):
    global labelSet
    baseUrl = '/'.join(imageTocUrl.split('/')[0:-1])
    resp = urllib2.urlopen(imageTocUrl)
    imgList = []
    for img in resp:
        imgList.append('/'.join([baseUrl, img.strip()]))
    print 'Last one: %s' % imgList[-1]
    print 'Image count: %d' % len(imgList)
    fraction = n_images / len(imgList)
    print 'Fraction: %f' % fraction
    # generate() is used to permit incremental output, to avoid HTTP process timeouts as this long process runs
    def generate():
        for img in imgList:
            if random.random() < fraction:
                labels = [x.lower() for x in detectLabelsUri(img)]
                # Here: write each img, label to REST client
                yield '%s: %s\r\n' % (img.split('/')[-1], json.dumps(labels))
                for label in labels:
                    labelSet.add(label)
        redisConn.set(labelSetRedisKey, pickle.dumps(labelSet))
    return Response(generate(), mimetype='text/plain')

# Dump the current set of labels
@app.route('/getLabelSet')
def getLabelSet():
    return json.dumps(sorted(labelSet))

# Generate the set of terms from the product descriptions,  populate termSet
@app.route('/genTermSet')
def genTermSet():
    global termSet
    resp = urllib2.urlopen(imageTocUrl)
    wordFreq = defaultdict(int)
    for fileName in resp:
        for word in fileName.lower().split('-')[-1].split('.')[0].split('_'):
            if len(word) > 2:
                wordFreq[word] += 1
    wordList = sorted(wordFreq.items(), key=lambda x: (-x[1], x[0]))[0:MAX_TERMS]
    wordList = [x[0] for x in wordList]
    termSet = set(wordList)
    redisConn.set(termSetRedisKey, pickle.dumps(termSet))
    return json.dumps(wordList)

# Dump the current set of terms
@app.route('/getTermSet')
def getTermSet():
    return json.dumps(sorted(termSet))


if __name__ == '__main__':
    print 'Starting %s on port %d' % (__file__, port)
    app.run(host='0.0.0.0', port=port, threaded=not DEBUG, debug=DEBUG)
