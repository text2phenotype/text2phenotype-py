import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'Sample_MR_Mr_H_page_0000.png'),
        os.path.join(base_dir, 'Sample_MR_Mr_H_page_0001.png'),
        os.path.join(base_dir, 'Sample_MR_Mr_H_page_0002.png'),
        os.path.join(base_dir, 'Sample_MR_Mr_H_page_0003.png')]

filepaths = (os.path.join(base_dir, 'Sample_MR_Mr_H.pdf'),
             os.path.join(base_dir, 'Sample_MR_Mr_H_result.json'),
             pngs)
