import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0000.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0001.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0002.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0003.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0004.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0005.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0006.png'),
        os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_page_0007.png')]

filepaths = (os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014.pdf'),
             os.path.join(base_dir, 'Steven_Keating_Pathology_Dec29_2014_result.json'),
             pngs)
