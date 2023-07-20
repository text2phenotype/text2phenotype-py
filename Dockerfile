# syntax=docker/dockerfile:experimental
# Use a reasonable FROM image
FROM python:3.8-buster

# Set environment variables
# UNIVERSE_IS_VERBOSE enables log level INFO.
ENV UNIVERSE_IS_VERBOSE=true

### Application metadata
ENV APP_NAME="text2phenotype-py"
ENV APP_BASE_DIR="/text2phenotype-py"
ENV PATH="${APP_BASE_DIR}/bin/:${PATH}"

# Set some container options
WORKDIR "${APP_BASE_DIR}"

###  This section should be ordered in such a way that the least likely
### operation to change should be first.

RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt apt-get update && \
  rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache && \
  apt-get install -y \
    apt-transport-https \
    apt-utils \
    build-essential \
    ca-certificates \
    ghostscript \
    imagemagick \
    parallel \
    pkg-config \
    poppler-utils \
    python3-all-dev \
    python3-pip \
    software-properties-common \
    unattended-upgrades- \
    unzip && \
    apt-get autoremove -y

# Copy the application code.
COPY --chown=5001:5001 . "${APP_BASE_DIR}"

RUN --mount=type=cache,target=/root/.cache --mount=type=cache,target=/tmp/download \
  pip install -r "${APP_BASE_DIR}/build-resources/config/python-requirements.txt" && \
  pip install -e "${APP_BASE_DIR}" && \
  chown -R 5001:5001 "${APP_BASE_DIR}/text2phenotype.egg-info" && \
  mv -v ${APP_BASE_DIR}/build-resources/bin/* "${APP_BASE_DIR}/bin/" && \
  mv -v ${APP_BASE_DIR}/build-tools/bin/* "${APP_BASE_DIR}/bin/" && \
  "${APP_BASE_DIR}/bin/docker-pre-build.sh" && \
  python -c "import nltk; nltk.download('averaged_perceptron_tagger', download_dir='/tmp/download/nltk_data'); nltk.download('punkt', download_dir='/tmp/download/nltk_data')" && \
  cp -a /tmp/download/nltk_data /usr/local/

# Do not include an ENTRYPOINT or CMD unless it is explicitly required.
# This container is designed to be the base of other containers which rely upon text2phenotype-py.
# Any container that FROMs this container is responsible for service start.

