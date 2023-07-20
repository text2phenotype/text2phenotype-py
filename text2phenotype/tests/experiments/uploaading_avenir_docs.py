# from text2phenotype.tagtog.tag_tog_client_data_source import TagTogClientDataSource
#
# tc_client = TagTogClientDataSource(project='demographics', proj_owner='tagtogadmin')
#
# # tc_client.upload_text_from_text2phenotype_nlp_out(
# #     prediction_file_extension='disease_sign.json',
# #     member_list='master',
#     local_pred_parent_dir = '/Users/shannon.fee/Downloads/text2phenotype-us-west-2/outbox/pre_sales/avanir_400',
#     tag_tog_subfolder='avanir_400'
#
# )


### uplaoding annotaiton for files already in tagtog
# tc_client.add_ann_2_docs_from_nlp_output(
#     prediction_file_extension='disease_sign.json',
#     member_list=['CEPuser', 'tagtogadmin'],
#     text2phenotype_api_out_dir='/Users/shannon.fee/Downloads/text2phenotype-us-west-2/outbox/tag_tog_prelabel/us-west-2'
#
# # )
## gettign all document ids to create an assignment sheet
# import pandas as pd
# a=tc_client.tag_tog_client.search('*')
# a= [b for b in a if not b['members_anncomplete']]
# df = pd.DataFrame(a)
# df = df['filename']
# df.to_csv('/Users/shannon.fee/Documents/demographics_assignment.csv')
# print(a)

