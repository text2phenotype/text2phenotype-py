import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'Sample_MR_LH_page_0000.png'),
        os.path.join(base_dir, 'Sample_MR_LH_page_0001.png'),
        os.path.join(base_dir, 'Sample_MR_LH_page_0002.png'),
        os.path.join(base_dir, 'Sample_MR_LH_page_0003.png'),
        os.path.join(base_dir, 'Sample_MR_LH_page_0004.png'),
        os.path.join(base_dir, 'Sample_MR_LH_page_0005.png')]

filepaths = (os.path.join(base_dir, 'Sample_MR_LH.pdf'),
             os.path.join(base_dir, 'Sample_MR_LH_result.json'),
             pngs)
