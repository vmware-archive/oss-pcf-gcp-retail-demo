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
import os, sys
import urllib2
import random
import json
import base64
from pcfgcp import PcfGcp
from google.cloud import language
from google.cloud import vision

NUM_IMAGES = 10
pg = PcfGcp()

# This is required for using the Vision API
# Ref. https://cloud.google.com/vision/docs/best-practices
imgResizerUrl = None
imgSize = 640
vcapStr = os.getenv('VCAP_SERVICES')
vcap = json.loads(vcapStr)
for entry in vcap['user-provided']:
  if entry['name'] == 'image-resizing-service':
    imgResizerUrl = entry['credentials']['url']

def logMsg(args):
    print "[Instance: %s] %s" % (str(os.getenv("CF_INSTANCE_INDEX", 0)), args)

"""Returns a URL which will run the image through the image resizing app to ensure
it fits into the bounds suggested by the GCP Vision API, for label detection.

The return value here should be passed into the Vision API as the `source_uri`
(see below)

Requires this app to be bound to a user provided service pointing to the resizing
app (https://github.com/cf-platform-eng/image-resizing-service)
"""
def getResizedImageUrl(origUrl):
  # http://localhost:18080/?size=256&urlBase64=aHR0cDoL3...QmlcGc=
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
    labels.append(label.description)
  return labels

"""
The argument provided here is the URL to a text file containing just the file names
to the images.  These files are assumed to be located within the same bucket as the
images, so the URL to each of the images is constructed based on this assumption.
"""
if len(sys.argv) < 2:
  print 'Usage: %s image_TOC_URL' % sys.argv[0]
  sys.exit(1)

tocUrl = sys.argv[1]
baseUrl = '/'.join(tocUrl.split('/')[0:-1])
resp = urllib2.urlopen(tocUrl)
imgList = []
for img in resp:
  imgList.append('/'.join([baseUrl, img.strip()]))
print 'Last one: %s' % imgList[-1]
print 'Image count: %d' % len(imgList)
fraction = NUM_IMAGES/len(imgList)
print 'Fraction: %f' % fraction
labelSet = set()
for img in imgList:
  if random.random() < fraction:
    labels = detectLabelsUri(img)
    for label in labels:
      labelSet.add(label.lower())
print "['" + "', '".join(sorted(labelSet)) + "']"

