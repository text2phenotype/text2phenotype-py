#!/usr/bin/env bash

###
# Import utilities
source "./build-tools/bin/build.utils"

###
# Variables

# UNIVERSE_IS_VERBOSE enables log level INFO.
UNIVERSE_IS_VERBOSE=true

log.info "> Start unit testing..."

log.info "> Creating Google credentials file..."
echo "${GOOGLE_APPLICATION_CREDENTIALS_JSON//BASE64::}" | base64 -d > ./google_application_credentials.json

TMP_PROJ="$(date +%s)-$RANDOM"

# Build any required resources
log.info ">> docker-compose build..."
docker-compose -p $TMP_PROJ --file docker-compose-tests-unit.yaml build

# Stand up the test stack
log.info ">> docker-compose up..."
docker-compose -p $TMP_PROJ --file docker-compose-tests-unit.yaml up --exit-code-from text2phenotype-py
unit_test_result=$?

# Cleanup docker-compose
log.info ">> docker-compose down..."
docker-compose -p $TMP_PROJ --file docker-compose-tests-unit.yaml down

log.info "> Unit testing complete. ('${unit_test_result}')"
exit ${unit_test_result}
