#!/usr/bin/env bash

###
# Import utilities
source "./build-tools/bin/build.utils"

###
# Variables

# UNIVERSE_IS_VERBOSE enables log level INFO.
UNIVERSE_IS_VERBOSE=true

log.info "> Start integration testing..."

TMP_PROJ=$(date +%s)

# Build any required resources
log.info ">> docker-compose build..."
docker-compose -p $TMP_PROJ --file docker-compose-tests-integration.yaml build

# Stand up the test stack
log.info ">> docker-compose up..."
docker-compose -p $TMP_PROJ --file docker-compose-tests-integration.yaml up --exit-code-from text2phenotype-py
integration_test_result=$?

# Cleanup docker-compose
log.info ">> docker-compose down..."
docker-compose -p $TMP_PROJ --file docker-compose-tests-integration.yaml down

log.info "> Integration testing complete. ('${integration_test_result}')"
exit ${integration_test_result}
