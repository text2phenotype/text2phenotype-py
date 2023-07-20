#!/usr/bin/env bash

set -o pipefail
set -e

### Pip version considerations ###
# Typical valid Pip versions in order they will be installed with text2phenotype>=1.1.0
# text2phenotype>=1.2.0 will SKIP everything but the final release. 
# Prereleased versions are not quite considered 1.2.0 (it's like 1.1.99999 or something)
# pip & pip-compile will require the --pre option to install any prerelease versions

# From lowest precedence to highest - i.e. dev will be chosen last, and final release chosen first
# 1.2.0.dev1  Development release - prerelease and devopment release
# 1.2.0a1     Alpha Release - prerelease
# 1.2.0b1     Beta Release - prerelease
# 1.2.0rc1    Release Candidate - prerelease
# 1.2.0       Final Release


# Check for Twine vars for uploading
for twine_var in TWINE_USERNAME TWINE_REPOSITORY_URL TWINE_PASSWORD; do
  if [[ ! -n ${!twine_var} ]]; then
    echo "Missing $twine_var from environment"
    exit 1
  fi
done

NEXUS_URL="https://nexus.text2phenotype.com/service/rest/repository/browse/pypi-lifesciences"

export TEXT2PHENOTYPE_PY_VERSION=$(git describe --tags)

echo -n ">> Fixing up version ${TEXT2PHENOTYPE_PY_VERSION} to "
# We tag as 14.0.14_dev for example, but the repo will store as 14.0.14.dev0
# If tag is rc then no .
if [[ ${TEXT2PHENOTYPE_PY_VERSION} =~ dev[0-9]+$ ]]; then
  TEXT2PHENOTYPE_PY_REPO_VER=$( echo $TEXT2PHENOTYPE_PY_VERSION | tr '-' '.' )
else
  TEXT2PHENOTYPE_PY_REPO_VER=$( echo $TEXT2PHENOTYPE_PY_VERSION | tr -d '-' )
fi
echo "$TEXT2PHENOTYPE_PY_REPO_VER"

echo ">> Querying Nexus Repo to determine text2phenotype package v: $TEXT2PHENOTYPE_PY_REPO_VER build status..."
http_code=$( \
  curl -so /dev/null \
  --connect-timeout 10 \
  -w "%{http_code}" \
  ${NEXUS_URL}/text2phenotype/${TEXT2PHENOTYPE_PY_REPO_VER}/ \
)

### If the package does not exist in repo, lets build it
if [[ ! $http_code == 200 ]]; then
  date; echo ">>> Starting text2phenotype package build..."
  if ! pip3 show build; then
    pip3 install build
  fi
  python3 -m build
  date; echo ">>> Finished text2phenotype package build..."

  for pkg in `ls dist/`; do
    if which twine; then
      twine upload "dist/$pkg"
    else
      pip3 install twine
      twine upload "dist/$pkg"
    fi
  done

else
  echo ">> The text2phenotype-$TEXT2PHENOTYPE_PY_REPO_VER package already exists in repo, skipping build..."
  exit 0
fi
