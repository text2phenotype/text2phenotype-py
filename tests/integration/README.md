# Integration Tests

These integration tests check the whole Text2phenotype's pipeline. In general, the test cases use **Text2phenotype API** to launch jobs and fetch metadata JSONs to validate the expected result.

Integration tests are disabled for CI jobs because it requires a prepared environment with all services and workers (not easy to deploy everything on each git-push of code). But it is useful tool for manual testing that allows checking in a half-automated way that the whole pipeline works.

There are several pipeline test-cases implemented:
* Document processing (text, file, corpus-job, App-Ingest)
* Job reprocess
* Job stop

# Configuration

There is `config-template.yaml` file with minimal required configuration. You should create `config.yaml` file based on this template and update a couple of variables. By default, `config-template.yaml` contains configuration for the **Alpha** environment.

Need to configure URL and Secret Key for **Meda API** service:
* `MDL_COMN_TEXT2PHENOTYPE_API_BASE`
* `MDL_COMN_TEXT2PHENOTYPE_API_SECRET_KEY`

Also need to configure S3 bucket/locations for the Corpus Job:
* `MDL_TEST_CORPUS_SOURCE_BUCKET`
* `MDL_TEST_CORPUS_SOURCE_DIRECTORY`
* `MDL_TEST_CORPUS_DESTINATION_DIRECTORY`
