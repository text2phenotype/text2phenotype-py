#!/usr/bin/env bash

if [[ -x build-tools/bin/suite-runner ]]; then
    # export DOCKER_FROM_REPO='text2phenotype-py'
    export DOCKER_NORMAL_BUILD='true'
    export DOCKER_IMAGE_CLEANUP='false'
    export DOCKER_BUILDKIT=1

    build-tools/bin/suite-runner
    # if [[ -x build-tools/bin/stage.deploy ]]; then
    #     for branch in dev master; do
    #       build-tools/bin/stage.deploy \
    #         --deploy-clusters "dev-ci-eks" \
    #         --deploy-branches "$branch" \
    #         --deploy-name "mdl-text2phenotype-api-ci-${branch}"
    #     done
    # else
    #     echo "The script does not exist or did not have execute permissions: build-tools/bin/stage.deploy"
    #     stat build-tools/bin/stage.deploy || true
    # fi
else
    echo "The script does not exist or did not have execute permissions: ../build-tools/bin/suite-runner"
    stat build-tools/bin/suite-runner
fi
