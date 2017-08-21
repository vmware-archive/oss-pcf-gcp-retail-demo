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

import json
import os
from operator import itemgetter
import base64
import tempfile

from google.cloud import storage
from google.cloud import language
from google.cloud import vision
from google.cloud.vision.image import Image
from google.oauth2.service_account import Credentials

"""Base class for accessing Google Cloud Platform services from Python apps
deployed to PCF.  This class implements the authentication part.

Here are the various service names, as defined in

  https://github.com/GoogleCloudPlatform/gcp-service-broker/blob/master/brokerapi/brokers/models/service_broker.go

const StorageName = "google-storage"
const BigqueryName = "google-bigquery"
const BigtableName = "google-bigtable"
const CloudsqlName = "google-cloudsql"
const PubsubName = "google-pubsub"
const MlName = "google-ml-apis"

"""
class PcfGcp:
  def __init__(self):
    self.VCAP_SERVICES = None
    self.clients = {
      'storage': None
      , 'google-bigquery': None
      , 'google-bigtable': None
      , 'google-cloudsql': None
      , 'google-pubsub': None
      , 'language': None
      , 'vision': None
    }
    self.projectId = None
    self.bucketName = None # Storage

  def className(self):
    return self.__class__.__name__

  def getClient(self, name):
    return self.clients.get(name)

  def setClient(self, name, val):
    self.clients[name] = val

  def get_service_instance_dict(self, serviceName): # 'google-storage', etc.
    vcapStr = os.environ.get('VCAP_SERVICES')
    if vcapStr is None:
      raise Exception('VCAP_SERVICES not found in environment variables (necessary for credentials)')
    vcap = json.loads(vcapStr)
    svcs = None
    try:
      svcs = vcap[serviceName][0]
    except:
      raise Exception('No instance of ' + serviceName + ' available')
    return svcs

  """serviceName is one of the keys in clients
  """
  def get_google_cloud_credentials(self, serviceName):
    """Returns oauth2 credentials of type
    google.oauth2.service_account.Credentials
    """
    service_info = self.get_service_instance_dict(serviceName)
    pkey_data = base64.decodestring(service_info['credentials']['PrivateKeyData'])
    pkey_dict = json.loads(pkey_data)
    self.credentials = Credentials.from_service_account_info(pkey_dict)
    # Get additional fields
    self.projectId = service_info['credentials']['ProjectId']
    print 'ProjectID: %s' % self.projectId
    if 'bucket_name' in service_info['credentials']:
      self.bucketName = service_info['credentials']['bucket_name']
    # Set the environment variable for GCP (this was the only way I could get Storage to work)
    credFile = tempfile.gettempdir() + '/' + 'GCP_credentials.json'
    with open(credFile, 'w') as out:
      out.write(pkey_data)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credFile
    print 'Wrote credentials to %s' % credFile
    print 'Set env GOOGLE_APPLICATION_CREDENTIALS to %s' % os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    return self.credentials

  """This can't be generic since the Client varies across services"""
  def getClient(self, serviceName):
    if self.clients[serviceName] is None:
      self.clients[serviceName] = language.Client(self.get_google_cloud_credentials(serviceName))
    return self.clients[serviceName]

  """Ref. https://cloud.google.com/natural-language/docs/sentiment-tutorial

    score ranges from -1.0 to 1.0
    magnitude ranges from 0.0 to Infinite (depends on length of document)

  """

  def getLanguage(self):
    if self.clients['language'] is None:
      self.clients['language'] = language.Client(self.get_google_cloud_credentials('google-ml-apis'))
    #print 'projectId: %s' % self.projectId
    return self.clients['language']

  """Ref. https://cloud.google.com/vision/docs/reference/libraries#client-libraries-install-python"""
  def getVision(self):
    if self.clients['vision'] is None:
      self.clients['vision'] = vision.Client(project=self.projectId,
        credentials=self.get_google_cloud_credentials('google-ml-apis'))
    return self.clients['vision']

  def getStorage(self):
    if self.clients['storage'] is None:
      self.get_google_cloud_credentials('google-storage')
      self.clients['storage'] = storage.Client(self.projectId)
    return self.clients['storage']

  def getBucketName(self):
    return self.bucketName

  def getBigQuery(self):
    pass

  def getBigtable(self):
    pass

  def getCloudSql(self):
    pass

  def getPubSub(self):
    pass

