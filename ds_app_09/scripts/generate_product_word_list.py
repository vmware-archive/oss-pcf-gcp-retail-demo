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

import sys, urllib2, re
from collections import defaultdict

"""
The argument provided here is the URL to a text file containing just the file names
to the images.  The file names are encoded with the SKU, the price, and the item
description; e.g. 105684-110-Berry_Premium_Rib_Texture_Tailored_Jacket.jpg

Generate a List of the distinct terms, ordered alphabetically.
"""

MAX_TERMS = 250

if len(sys.argv) < 2:
  print 'Usage: %s image_TOC_URL' % sys.argv[0]
  sys.exit(1)

tocUrl = sys.argv[1]
resp = urllib2.urlopen(tocUrl)

wordFreq = defaultdict(int)
for fileName in resp:
  for word in fileName.lower().split('-')[-1].split('.')[0].split('_'):
    if len(word) > 2:
      wordFreq[word] += 1

wordList = sorted(wordFreq.items(), key=lambda x: (-x[1], x[0]))[0:MAX_TERMS]
wordList = [x[0] for x in wordList]
print wordList

