from setuptools import setup, find_packages
from codecs import open
from os import path, environ

from text2phenotype.common.test_command import TestCommand

try:
    version = environ["TEXT2PHENOTYPE_PY_VERSION"]
except KeyError:
    version = '0.1.0'
    print('Environment variable TEXT2PHENOTYPE_PY_VERSION not found, using old compatible default.')

package_dir = path.abspath(path.dirname(__file__))
with open(path.join(package_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


def parse_requirements(file_path):
    with open(file_path, 'r') as reqs:
        req_list = []
        for line in reqs.readlines():
            if line.startswith('#'):
                continue
            if line.startswith('-r '):
                sub_req = parse_requirements(f"{line.split('-r ')[-1].replace('/n', '').strip()}")
                req_list.extend(sub_req)
                continue
            req_list.append(line)
        return req_list


installation_requirements = parse_requirements('requirements.txt')

setup(
    name='text2phenotype',
    version=version,
    description=long_description,
    long_description=long_description,
    url='https://github.com/text2phenotype/text2phenotype-py',
    author='Text2phenotype',
    author_email='',
    license='Other/Proprietary License',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Healthcare Industry',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords='text2phenotype common python library',
    packages=find_packages(exclude=['tests']),
    install_requires=installation_requirements,
    extras_require={
        'dev': ['ipython'],
    },
    tests_require=['pytest'],
    cmdclass={'test': TestCommand},
    include_package_data=True,
)
