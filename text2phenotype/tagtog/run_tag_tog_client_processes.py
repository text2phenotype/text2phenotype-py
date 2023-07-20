import argparse

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment
from text2phenotype.tagtog.tag_tog_client_data_source import TagTogClientDataSource


def parse_arguments():
    """
    this parses the argument passed into the terminal
    """
    parser = argparse.ArgumentParser()
    # args you need for all possible operations
    parser.add_argument('-project', type=str,
                        help='tag_tog project folder name (name of unzipped folder)')
    parser.add_argument('-proj_owner', type=str, help='The owner of the tag tog project (username)')
    parser.add_argument('-parent_dir', type=str, help='where you want to write intermediate files out to, '
                                                       'required for saving raw text and prelabeling')
    parser.add_argument('--subfolder', type=str, help='Tag Tog Project Subfolder, required for pushing pdfs and '
                                                      'getting raw text')

    # operation 1: push pdfs to tag tog
    parser.add_argument('--upload_pdfs', action='store_true',
                        help='whether to push local pdfs, if included, you much also provide a local_pdf_dir')
    parser.add_argument('--local_pdf_dir', type=str, help='Local Directory containing pdfs you want to uplaod to tag tog')

    # operation 2: download html files from tag tog and get raw text
    parser.add_argument('--get_raw_text', action='store_true',
                        help='Whether to download html files from tag tog and create a directory of just the '
                             'appropriate extracted raw text files to be passed to text2phenotype-ap')
    # used for operations 3 and 4
    parser.add_argument('--text2phenotype_api_out_dir', type=str, help='Local copy of the text2phenotype-api output information')
    parser.add_argument('--text2phenotype_ext', type=str,
                        help='Which file extension your results can be found in ie: covid_specific.json')
    parser.add_argument('--member_list', type=list, help='Tag Tog user ids that you want to overwrite with annotations')


    # operation 3: prelabel pdfs and push to tag tog
    parser.add_argument('--add_annotations', action='store_true',
                        help='whether to use the text2phenotype_api_output files to add pre-predictions to files')


    #operation 4: use text and text2phenotype-api output files to push to tag tog
    parser.add_argument(
        '--prelabel_text2phenotype_api_text', action='store_true',
        help='If true use the .extracted_text.txt and the annotation in the text2phenotype_ext to push prelabelss to tag tog')
    parser.add_argument(
        '--split_text', action='store_true',
        help='If set will split text documents to max length specified by env variable')

    return parser.parse_args()


def run_tasks(parsed_args):
    data_source = TagTogClientDataSource(**parsed_args)

    if parsed_args.get('upload_pdfs'):
        if not parsed_args.get('local_pdf_dir'):
            raise ValueError('Trying to upload pdfs without specifying a local directory of pdfs')
        data_source.push_local_pdfs_to_tag_tog(
            pdfs_dir=parsed_args.get('local_pdf_dir'),
            subfolder=parsed_args.get('subfolder'))

    if parsed_args.get('get_raw_text'):
        if not parsed_args.get('local_text_dir'):
            operations_logger.warning("No Local_text_dir found, writing text to /tmp")
        data_source.fill_html_and_text_folders(
            local_text_dir=parsed_args.get('local_text_dir', '/tmp'),
            subfolder=parsed_args.get('subfolder', 'pool'))

    if parsed_args.get('add_annotations'):
        data_source.add_ann_2_docs_from_nlp_output(
            prediction_file_extension=parsed_args.get('text2phenotype_ext'),
            text2phenotype_api_out_dir=parsed_args.get('text2phenotype_api_out_dir'),
            member_list=parsed_args.get('member_list')
        )

    if parsed_args.get('prelabel_text2phenotype_api_text'):
        data_source.upload_text_from_text2phenotype_nlp_out(
            prediction_file_extension=parsed_args.get('text2phenotype_ext'),
            local_pred_parent_dir=parsed_args.get('text2phenotype_api_out_dir'),
            tag_tog_subfolder=parsed_args.get('subfolder'),
            member_list=parsed_args.get('member_list')
        )


if __name__ == '__main__':
    Environment.load()
    parsed_args = vars(parse_arguments())
    run_tasks(parsed_args=parsed_args)