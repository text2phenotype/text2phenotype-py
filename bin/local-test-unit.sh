#!/bin/bash

# GOOGLE_APPLICATION_CREDENTIALS_JSON is needed and is a secret
export GOOGLE_APPLICATION_CREDENTIALS="$CI_PROJECT_DIR/google_application_credentials.json"
export MDL_COMN_TEXT2PHENOTYPE_SAMPLES_PATH="$CI_BUILDS_DIR/data-management/nlp/text2phenotype-samples"

python3 -m virtualenv venv
echo "${GOOGLE_APPLICATION_CREDENTIALS_JSON#BASE64::}" | base64 -d > "$GOOGLE_APPLICATION_CREDENTIALS"
venv/bin/pip install --use-feature=2020-resolver .
venv/bin/python nltk_download.py

venv/bin/python -m pytest tests/ --junitxml=${UNIT_TESTS_REPORT_FILE:-junit-report.xml}
