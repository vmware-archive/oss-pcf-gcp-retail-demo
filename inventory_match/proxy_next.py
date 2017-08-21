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

"""

All this code does is extend ProxyRequestHandler from "proxy2", and override
a couple of things so it stores images from the NEXT clothing retailer
web site (http://www.next.co.uk/), encoding the following data into the
file names:

  * item number
  * price (units are English pound)
  * item description, with underscores replacing any space or other non-word characters

I forked proxy2 here: https://github.com/mgoddard-pivotal/proxy2.git

To run this:

  * clone this fork
  * cd into the new directory, "proxy2"
  * copy this file into ./
  * ./proxy_next.py
  * Configure your computer to use this proxy, running on localhost:3123
  * Go to that NEXT web site and start to browse categories of clothing
  * You should begin to accumulate images in "crawl_data/"

"""

import sys
import os
import re
from lxml import html
import urllib
import proxy2

# Encode item number, price, and description into file name
def genFileName(item_num, price, desc, img_url):
  desc = re.sub(r'[^\w_]+', '_', desc)
  mat = re.match(r'^.+?(\d+)$', price)
  if mat:
    price = mat.group(1)
  mat = re.match(r'.+/([^/]+)\.(\w+).*$', img_url)
  if mat:
    if item_num == mat.group(1):
      print "Item number matches URL"
    else:
      print "Item number DOES NOT MATCH URL"
    ext = mat.group(2)
  return '-'.join([item_num, price, desc]) + '.' + ext

# As currently set up, this just puts all data into ./crawl_data
def getDataDir():
  return os.path.join(os.getcwd(), 'crawl_data')

def saveImage(item_num, price, desc, img_url):
  print 'In saveImage(%s)' % img_url
  if not os.path.isdir(getDataDir()):
    os.mkdir(getDataDir())
  img_file = os.path.join(getDataDir(), genFileName(item_num, price, desc, img_url))
  if not os.path.isfile(img_file):
    fh = urllib.urlopen(img_url, proxies={}) # We must ignore *this* proxy here
    with open(img_file, 'w') as f:
      f.write(fh.read())
    fh.close()

class NextRequestHandler(proxy2.ProxyRequestHandler):

    def __init__(self, *args, **kwargs):
        proxy2.ProxyRequestHandler.__init__(self, *args, **kwargs)

    # Crawl the NEXT clothing retailer site
    def save_handler(self, req, req_body, res, res_body):
      if req.path.startswith('http://www.next.'):
        print 'URL is good (%s)' % req.path
        if res_body is not None:
          content_type = res.headers.get('Content-Type', '')
          if content_type.startswith('text/html'):
            tree = html.fromstring(res_body)
            articles = tree.xpath('//article[contains(@class, "Item") and contains(@class, "Fashion")]')
            for i, article in enumerate(articles):
              item_num = article.xpath('@data-itemnumber')[0]
              print 'Item number: %s' % item_num
              desc = article.xpath('//a[@class="TitleText"]/text()')[i]
              print 'Title: %s' % desc
              price = article.xpath('//div[@class="Price"]/a/text()')[i]
              print 'Price: %s' % price
              img_url = article.xpath('//div[@class="Images"]/a/img/@src')[i]
              print 'Image URL: %s' % img_url
              print ''
              saveImage(item_num, price, desc, img_url)

def start(HandlerClass=NextRequestHandler, ServerClass=proxy2.ThreadingHTTPServer, protocol="HTTP/1.1"):
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 3123
    server_address = ('', port)

    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    print "Serving HTTP Proxy on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()


if __name__ == '__main__':
  pid = str(os.getpid())
  pid_file = os.path.basename(sys.argv[0]) + '.pid'
  with open(pid_file, 'w') as f:
    f.write(pid + '\n')
  start()

