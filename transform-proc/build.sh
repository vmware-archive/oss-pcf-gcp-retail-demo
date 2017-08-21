#!/bin/bash

# Set the environment with VCAP_SERVICES
export VCAP_SERVICES=`cat ./VCAP_SERVICES.json`

# Set the parameter for service-name
mvn -Dservice-name=ds_app_09-service clean package

