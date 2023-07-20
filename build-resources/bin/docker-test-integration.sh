#!/usr/bin/env bash

# Source the bash.utils
source "${APP_BASE_DIR}/bin/bash.utils"

# log.info "> Installing python ${APP_BASE_DIR}/requirements/test.txt..."
# pip install --no-cache-dir -r "${APP_BASE_DIR}/requirements/test.txt"

log.info "> Running integration tests..."
log.info "> No integration tests. Skipping."
# python ./run_tests.py
# exit_code=$?
exit_code=0

log.info "> Integration tests complete. Exited ('${exit_code}')"
exit ${exit_code}
