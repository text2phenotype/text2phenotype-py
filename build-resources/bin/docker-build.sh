#!/usr/bin/env bash

### THIS FILE IS NOT USED

set -e

# Source the bash.utils
source "${APP_BASE_DIR}/bin/bash.utils"

# Text2phenotype-py will only be installed system level
log.info "> Installing ${APP_NAME}..."
# pip install -e "${APP_BASE_DIR}"

log.info ">> Installing ${APP_BASE_DIR}/nltk-download.py..."
# System and user specific installs during migration away from root
# python "${APP_BASE_DIR}/nltk_download.py"
# su -c "python ${APP_BASE_DIR}/nltk_download.py" mdluser

log.info "> ${APP_NAME} installation complete."
