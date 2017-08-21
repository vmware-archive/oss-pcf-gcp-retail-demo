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

#
# After `cf push` of the image resizing service (https://github.com/cf-platform-eng/image-resizing-service),
# run this to create a user provided service that you will then bind to this ds_app_09, so images being
# analyzed by Vision API will have the correct size.
#

# SET THIS TO THE URL FOR YOUR INSTANCE
image_resizer_url="http://image-resizing-service.YOUR_PCF_INSTALL.DOMAIN"

cf cups image-resizing-service -p "{ \"url\": \"$image_resizer_url\" }"

