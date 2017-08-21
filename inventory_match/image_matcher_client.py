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

import urllib
import base64
import json
import sys
import os

MATCHER_URL = 'http://image-match.apps.YOUR_DOMAIN/query_image_url' # Append '/' + url

# Provide a URL and number of items on the command line
imgUrl = None
if len(sys.argv) == 3:
  imgUrl = sys.argv[1]
  nItems = sys.argv[2]
else:
  print 'Usage: %s http://some.image.url/file.jpg NUMBER' % sys.argv[0]
  sys.exit(1)

resp = urllib.urlopen(MATCHER_URL + '/' + nItems + '/' + base64.b64encode(imgUrl))
match = json.loads(resp.read())
print '\nQuery URL: %s' % imgUrl
for item in match:
  # { 'sku': sku, 'price': price, 'desc': desc, 'url': url }
  print
  print '\tSKU: %s' % item['sku']
  print '\tDescription: %s' % item['desc']
  print '\tPrice: %s' % item['price']
  print '\tImage URL: %s' % item['url']

