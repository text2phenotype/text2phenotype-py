#!/usr/bin/env bash

# Source the bash.utils
source "${APP_BASE_DIR}/bin/bash.utils"

log.info "> Running unit tests..."
python setup.py test
exit_code=$?

log.info "> Unit tests complete. Exited ('${exit_code}')"
exit ${exit_code}
