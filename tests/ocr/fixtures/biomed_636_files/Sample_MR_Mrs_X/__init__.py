import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'Sample_MR_Mrs_X_page_0000.png'),
        os.path.join(base_dir, 'Sample_MR_Mrs_X_page_0001.png'),
        os.path.join(base_dir, 'Sample_MR_Mrs_X_page_0002.png'),
        os.path.join(base_dir, 'Sample_MR_Mrs_X_page_0003.png')]

filepaths = (os.path.join(base_dir, 'Sample_MR_Mrs_X.pdf'),
             os.path.join(base_dir, 'Sample_MR_Mrs_X_result.json'),
             pngs)
