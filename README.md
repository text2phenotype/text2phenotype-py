# text2phenotype-py

This project provides a core library shared by Text2phenotype services.

# Docker builds

There is now support for building and testing docker containers. This work is based on the github repository [text2phenotype/build-tools](https://github.com/text2phenotype/build-tools). Please refer to the documentation in that repository for more information.

# Package setup

There are non-code resources required for tests (*.txt, *.pdf, *.json files/fixtures). These rules defined in the `MANIFEST.in` and resurces will be included to the result package during setup.

[Python packaging documentation](https://packaging.python.org/guides/using-manifest-in/#manifest-in-commands)
