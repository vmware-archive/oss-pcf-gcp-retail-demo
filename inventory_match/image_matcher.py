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

from keras.applications.vgg16 import VGG16
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input
import numpy as np
import os, sys, glob
from scipy import sparse
import math
import time
import tempfile
from functools import partial

# For Web app
from flask import (Flask, request)
import re
import urllib
import urllib2
import cStringIO
import json
import base64

# For Storage
from pcfgcp import PcfGcp
from google.cloud import storage

app = Flask(__name__)
port = int(os.getenv("PORT", 18080))

# For testing with a subset of available images
import random
testFraction = 1.0 # Set to 1.0 to index all of the images

vgg16Model = None
imageTocUrl = os.getenv('IMAGE_TOC_URL')
if imageTocUrl is None:
  raise Exception('Environment variable "IMAGE_TOC_URL" must be set to the URL of a listing of image files')
imageBaseUrl = '/'.join(imageTocUrl.split('/')[:-1])
print 'imageTocUrl: %s, imageBaseUrl: %s' % (imageTocUrl, imageBaseUrl)

pg = PcfGcp()
storageClient = pg.getStorage()
bucketName = pg.getBucketName()
print 'Storage bucket: %s' % bucketName

modelFileName = 'image_match_model.zip'

# Parallel arrays
imageNames = []
imageFeatures = []

def getModelFullPath():
  tmpDir = tempfile.gettempdir()
  return tmpDir + '/' + modelFileName

# Save index for later use
def persistIndex():
  global imageNames
  global imageFeatures
  modelStore = tempfile.NamedTemporaryFile(delete=False)
  print 'Model store file: %s' % modelStore.name
  np.savez(modelStore, imageNames=imageNames, imageFeatures=imageFeatures)
  modelStore.close()
  # Upload this model to Storage
  bucket = storageClient.get_bucket(bucketName)
  blob = bucket.blob(modelFileName)
  blob.upload_from_filename(modelStore.name)
  if blob.exists():
    print 'Model uploaded to Storage'
  else:
    print 'Failed to upload model to Storage'

# Load an existing model, if it's there
def loadIndex():
  global imageNames
  global imageFeatures
  rv = False
  tmpDir = tempfile.gettempdir()
  modelFullPath = tmpDir + '/' + modelFileName
  # Check storage for it and pull it down
  bucket = storageClient.get_bucket(bucketName)
  blob = bucket.blob(modelFileName)
  if blob.exists():
    print 'Model found in Storage -- downloading'
    blob.download_to_filename(modelFullPath)
    modelStore = open(modelFullPath, 'r')
    npzfile = np.load(modelStore)
    imageNames = npzfile['imageNames']
    imageFeatures = npzfile['imageFeatures']
    modelStore.close()
    rv = True
  else:
    print 'Model not found in Storage -- will create fresh model'
  return rv

# Get the magnitude of vector a
def vecMag(a):
  magMatrix = a*a.transpose()
  return math.sqrt(magMatrix[0, 0])

# For vector a, return a/||a||, unit vector in the direction of a
def normalizedVec(a):
  return a/vecMag(a)

def imgFileFromUrl(url):
  return cStringIO.StringIO(urllib.urlopen(url).read())

def getImageFeatures(imagePath):
  global vgg16Model
  img = image.load_img(imagePath, target_size=(224, 224))
  x = image.img_to_array(img)
  x = np.expand_dims(x, axis=0)
  x = preprocess_input(x)
  if vgg16Model is None:
    print 'Loading VGG16 model'
    vgg16Model = VGG16(weights='imagenet', include_top=False)
    print 'Done'
  return normalizedVec(sparse.csr_matrix(vgg16Model.predict(x).flatten()))

# Create the index based off a list of URLs to images, where the image list
# contains the file name only, and all images are placed into the same directory
# as the list file.
def createIndex():
  global imageNames
  global imageFeatures
  tmpDir = tempfile.gettempdir()
  for fileName in urllib2.urlopen(imageTocUrl):
    fileName = fileName.strip()
    imageUrl = imageBaseUrl + '/' + fileName
    tmpFile = tmpDir + '/' + fileName
    if random.random() > testFraction:
      continue
    print 'Indexing %s now ...' % imageUrl
    urllib.urlretrieve(imageUrl, tmpFile)
    try:
      imageFeatures.append(getImageFeatures(tmpFile))
    except:
      continue
    os.remove(tmpFile)
    imageNames.append(fileName)

# This returns the same value as spatial.distance.cosine(a, b),
# but for sparse vectors (a, b)
def cosineDist(a, b):
  matVal = a*b.transpose()
  return 1.0 - matVal[0, 0]

# Serial version (saving for comparison with || version)
def imageSearch(imagePath, nItems):
  qVec = getImageFeatures(imagePath)
  distances = []
  for sVec in imageFeatures:
    distances.append(cosineDist(qVec, sVec))
  topNIndices = np.argsort(distances)[:nItems]
  topImageNames = []
  for idx in topNIndices:
    topImageNames.append(imageNames[idx])
  return topImageNames

def productInfoFromFileName(fileName):
  # Example fileName: "L57817-42-Miss_Selfridge_Polka_Dot_Wrap_Midi_Dress.jpg"
  (sku, price, desc) = fileName.split('-')
  desc = re.sub(r'_', ' ', desc.split('.')[0])
  url = imageBaseUrl + '/' + fileName
  return { 'sku': sku, 'price': price, 'desc': desc, 'url': url }

# Pass the image URL, base64 encoded
@app.route('/query_image_url/<int:nItems>/<urlBase64>')
def queryImageUrl(nItems, urlBase64):
  url = base64.b64decode(urlBase64)
  rv = []
  imgFile = imgFileFromUrl(url)
  for result in imageSearch(imgFile, nItems):
    rv.append(productInfoFromFileName(result))
  imgFile.close()
  return json.dumps(rv)

@app.route('/status')
def test():
  return "STATUS_OK"

if __name__ == '__main__':
  if not loadIndex():
    t0 = time.time()
    createIndex()
    et = time.time() - t0
    print 'Index creation took %d seconds' % et
    persistIndex()
  app.run(host='0.0.0.0', port=port, threaded=True, debug=False)

