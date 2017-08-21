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

# First: `conda install whoosh`

from whoosh.index import (create_in, open_dir)
from whoosh.fields import *
from whoosh.qparser import (QueryParser, FuzzyTermPlugin)
import urllib2
import re, os, sys

# List of all the images, where file names encode SKU-Price-The_Description_of_the_Item.jpg
# L58105-24-Pink_Clove_Lapel_Fitted_Midi_Dress.jpg
TOC_URL = "https://storage.googleapis.com/retail-image/toc.txt"
INDEX_DIR = './text_index'
FUZZ = '~2' # Ref. http://whoosh.readthedocs.io/en/latest/parsing.html#adding-fuzzy-term-queries

"""Only create the text index if INDEX_DIR is not present
"""
def index_docs():
  #schema = Schema(url=ID(stored=True), meta=TEXT(analysis.NgramWordAnalyzer(3)))
  schema = Schema(url=ID(stored=True), meta=TEXT)
  if not os.path.isdir(INDEX_DIR):
    os.mkdir(INDEX_DIR)
    ix = create_in(INDEX_DIR, schema)
    writer = ix.writer()
    resp = urllib2.urlopen(TOC_URL)
    for line in resp:
      line = line.strip()
      meta = ' '.join(re.split(r'[-_.]', line)[:-1])
      url = re.sub(r'/[^/]+$', '', TOC_URL) + '/' + line
      writer.add_document(meta=unicode(meta, 'utf-8'), url=unicode(url, 'utf-8'))
    writer.commit()
    ix.close()

if len(sys.argv) == 1:
  print 'Usage: %s some query string ...' % sys.argv[0]
  sys.exit(1)

index_docs()
ix = open_dir(INDEX_DIR)
with ix.searcher() as searcher:
  query_str = ' '.join(map(lambda word: word + FUZZ, sys.argv[1:]))
  print 'Query: "%s"' % query_str
  parser = QueryParser('meta', ix.schema)
  parser.add_plugin(FuzzyTermPlugin())
  query = parser.parse(unicode(query_str))
  results = searcher.search(query, limit=None) # Note the "limit=None" implies "unlimited"
  for result in results:
    print 'Result: ',
    print result

