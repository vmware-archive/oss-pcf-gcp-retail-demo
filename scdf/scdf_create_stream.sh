#!/bin/bash

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

# EDIT THESE VALUES
dataflow_url="http://dataflow-server.apps.YOUR_PCF_INSTALL.DOMAIN"
xform_jar="https://storage.googleapis.com/mgoddard-jars/v19/transform-proc-0.0.1-SNAPSHOT.jar"
sink_jar="https://storage.googleapis.com/mgoddard-jars/v17/offer-sink-0.0.1-SNAPSHOT.jar"

# Register apps
time curl -H "Accept: application/json" -X POST -d "uri=$xform_jar&force=true" $dataflow_url/apps/processor/xform-proc
time curl -H "Accept: application/json" -X POST -d "uri=$sink_jar&force=true" $dataflow_url/apps/sink/offer-sink

# Create stream
time curl -H "Accept: application/json" -X POST -d "name=socialmedia&definition=http | proc08: xform-proc --service-name=ds_app_09-service | proc14: xform-proc --service-name=ds_app_15-service | offer-sink&deploy=false" $dataflow_url/streams/definitions

# Deploy the stream
time curl -H "Accept: application/json" -X POST -d "properties=app.proc08.spring.cloud.deployer.cloudfoundry.services=ds_app_09-service,app.proc14.spring.cloud.deployer.cloudfoundry.services=ds_app_15-service" $dataflow_url/streams/deployments/socialmedia

