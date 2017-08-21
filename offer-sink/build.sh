#!/bin/bash

# Set the environment with VCAP_SERVICES
export VCAP_SERVICES=`cat ./VCAP_SERVICES.json`

mvn clean package

