import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'Sample_MR_Richard_Smith_page_0000.png'),
        os.path.join(base_dir, 'Sample_MR_Richard_Smith_page_0001.png')]

filepaths = (os.path.join(base_dir, 'Sample_MR_Richard_Smith.pdf'),
             os.path.join(base_dir, 'Sample_MR_Richard_Smith_result.json'),
             pngs)
