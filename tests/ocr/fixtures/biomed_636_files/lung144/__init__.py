import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'lung144_page_0000.png'),
        os.path.join(base_dir, 'lung144_page_0001.png'),
        os.path.join(base_dir, 'lung144_page_0002.png')]

filepaths = (os.path.join(base_dir, 'lung144.pdf'),
             os.path.join(base_dir, 'lung144_result.json'),
             pngs)
