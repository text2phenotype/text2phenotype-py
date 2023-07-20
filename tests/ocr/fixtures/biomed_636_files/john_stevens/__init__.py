import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'john_stevens_page_0000.png'),
        os.path.join(base_dir, 'john_stevens_page_0001.png'),
        os.path.join(base_dir, 'john_stevens_page_0002.png')]

filepaths = (os.path.join(base_dir, 'john_stevens.pdf'),
             os.path.join(base_dir, 'john_stevens_result.json'),
             pngs)
