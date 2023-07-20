import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'lung146_page_0000.png'),
        os.path.join(base_dir, 'lung146_page_0001.png')]

filepaths = (os.path.join(base_dir, 'lung146.pdf'),
             os.path.join(base_dir, 'lung146_result.json'),
             pngs)
