#!/usr/bin/env python3

import sys

from text2phenotype.common.log import operations_logger

from text2phenotype.constants.environment import Environment

from text2phenotype.tasks.rmq_worker import WorkerHealthcheckFile

def main():
    """
    CLI script to report on the status of the task worker healthcheck file.
    This script relies on environment variables set in the common text2phenotype-py
    environment constants function provided via text2phenotype.tasks.rmq_worker.
    """
    verbose_logging = Environment.WORKER_HEALTHCHECK_VERBOSE.value

    healthcheck = WorkerHealthcheckFile()
    file_path = healthcheck.filepath

    if healthcheck.exists():
        file_age_max = healthcheck.age_max()
        file_age_now = healthcheck.age_in_seconds()

        if healthcheck.is_expired():
            operations_logger.error(f"Task worker healthcheck ('{file_path}') "
                                    f"has expired: {file_age_now}s > {file_age_max}s")
            sys.exit(1)

        else:
            if verbose_logging:
                operations_logger.info(f"Task worker healthcheck ('{file_path}') "
                                       f"has not expired: {file_age_now}s < {file_age_max}s")
            sys.exit(0)

    else:
        if verbose_logging:
            operations_logger.info(f"Task worker healthcheck file ('{file_path}') "
                                   "does not exist. Exiting.")
        sys.exit(0)


if __name__ == '__main__':
    main()
