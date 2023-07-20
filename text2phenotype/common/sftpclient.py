import paramiko
import os
from text2phenotype.common.log import logger
from typing import Iterable, List


# TODO: refactor config into environment vars
class SftpClientConfig(object):
    host = 'try.qa.text2phenotype.com'
    port = 2222
    username = 'changeme'
    password = 'changeme'
    upload_path = '/uploads/text2phenotype'


paramiko.util.log_to_file('lightbeam.log')


def upload(fileset: Iterable) -> List:
    """
    :param fileset: provide a fileset (set or list) and upload over SFTP
    :return: list() of server responses, one per file
    """
    config = SftpClientConfig

    with paramiko.Transport((config.host, config.port)) as transport:
        transport.connect(username=config.username, password=config.password)
        with paramiko.SFTPClient.from_transport(transport) as sftp:
            res = list()
            for f in fileset:
                local_path = os.path.abspath(f)
                remote_path = os.path.join(config.upload_path, os.path.basename(f))
                logger.debug('local_path=' + local_path)
                logger.debug('remote_path=' + remote_path)
                res.append(sftp.put(local_path, remote_path))

            return res
