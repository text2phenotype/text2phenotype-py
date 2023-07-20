import os

from text2phenotype.constants.environment import Environment

ASPECT_SAMPLES_DIR = os.path.join(Environment.DATA_ROOT.value, 'biomed', 'aspect')


def sample_file(folder: str, filename: str):
    """
    :param folder: 'train' or 'test' or 'result'
    :param filename: str
    :return: str path to file
    """
    return os.path.join(ASPECT_SAMPLES_DIR, folder, filename)


def train_path(filename):
    return sample_file('train', filename)


def test_path(filename):
    return sample_file('test', filename)


def result_path(filename):
    return sample_file('result', filename)
