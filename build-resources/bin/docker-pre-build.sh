#!/usr/bin/env bash

set -e

# Debug
cat /etc/resolv.conf

# Source the bash.utils
source "${APP_BASE_DIR}/bin/bash.utils"

log.info "> Starting ${APP_NAME} build..."

# log.info ">> Installing ${APP_NAME} dependencies..."

# apt-get update -y

# apt-get upgrade -y

# log.info ">>> Purging all python2 packages"
# apt --yes --auto-remove purge python2 python2-minimal python2.7 libpython2.7

# apt-get install -y \
#   apt-transport-https \
#   apt-utils \
#   build-essential \
#   ca-certificates \
#   ghostscript \
#   imagemagick \
#   parallel \
#   pkg-config \
#   poppler-utils \
#   python3-pip \
#   python3-all-dev \
#   software-properties-common \
#   unattended-upgrades- \
#   unzip

log.info ">> Creating application user..."
useradd -u 5001 -U -c "Text2phenotype App User" -m -d /app -s /bin/bash mdluser

# Requirements will only be installed system level
# log.info ">> Pip installing text2phenotype-py python-requirements..."
# pip install --no-cache-dir -r "${APP_BASE_DIR}/build-resources/config/python-requirements.txt"

# Security policy removal for convert/ghostscript
# https://stackoverflow.com/questions/52998331/imagemagick-security-policy-pdf-blocking-conversion
for PATTERN in PS PS2 PS3 EPS PDF XPS; do
  sed -i "/pattern=\"${PATTERN}\"/d" /etc/ImageMagick-6/policy.xml
done

# Add dumb-init to assist with proper signal handling
curl -Ls https://github.com/Yelp/dumb-init/releases/download/v1.2.0/dumb-init_1.2.0_amd64 -o /usr/local/bin/dumb-init
chmod +x /usr/local/bin/dumb-init

log.info ">> ${APP_NAME} dependency installation complete."
