import argparse

from text2phenotype.tagtog.tag_tog_async_data_source import TagTogAsyncDataSource
from text2phenotype.constants.features.label_types import deserialize_label_type


def parse_arguments():
    """
    this parses the argument passed into the terminal
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-project', type=str,
                        help='tag_tog project folder name (name of unzipped folder)')
    parser.add_argument('-parent_dir', type=str, help='directory the unzipped folder lives in locally')
    parser.add_argument('--include_master_annotations', action='store_true',
                        help='whether to include annotations from master copy')
    parser.add_argument('--require_complete', action='store_true',
                        help='whether to require annotations be marked as complete')
    parser.add_argument(
        "-label_type", type=str, default=None,
        help=("The expected label type class name, if annotations are only one type. "
              "E.g. 'LabLabel', 'DocumentTypeLabel'. "
              "Specify to avoid name collisions, eg between LabLabel and CovidLabLabel"))
    return parser.parse_args()


if __name__ == '__main__':
    parsed_args = vars(parse_arguments())
    if parsed_args["label_type"]:
        parsed_args["label_type"] = deserialize_label_type(parsed_args["label_type"])
    TagTogAsyncDataSource(**parsed_args).write_raw_materials_for_annotated_materials()
