import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'Sample_MR_L_Diaz_page_0000.png'),
        os.path.join(base_dir, 'Sample_MR_L_Diaz_page_0001.png'),
        os.path.join(base_dir, 'Sample_MR_L_Diaz_page_0002.png')]

filepaths = (os.path.join(base_dir, 'Sample_MR_L_Diaz.pdf'),
             os.path.join(base_dir, 'Sample_MR_L_Diaz_result.json'),
             pngs)
