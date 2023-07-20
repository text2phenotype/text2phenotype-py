import csv
import os

from text2phenotype.common import common
from typing import Dict, Any

ZIPCODE_FILE_CSV = 'free-zipcode-database.csv'
ZIPCODE_FILE_JSON = 'free-zipcode-database.json'


def relpath_csv(relpath: str='.', filename: str=ZIPCODE_FILE_CSV) -> str:
    return os.path.join(relpath, filename)


def relpath_json(relpath: str='.', filename: str=ZIPCODE_FILE_JSON) -> str:
    return os.path.join(relpath, filename)


def read_csv(relpath: str) -> Dict[Any, Dict[str, str]]:
    """
    :param relpath: http://federalgovernmentzipcodes.us/
    :return:
    """
    key_values = dict()

    csv_file = relpath_csv(relpath)

    with common.read_text(csv_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:
            zip5 = row[1]
            city = row[3]
            state = row[4]
            country = row[12]
            key_values[zip5] = {'city': city, 'state': state, 'country': country}

    return key_values
