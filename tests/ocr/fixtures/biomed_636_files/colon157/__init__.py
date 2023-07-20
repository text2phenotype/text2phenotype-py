import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'colon157_page_0000.png'),
        os.path.join(base_dir, 'colon157_page_0001.png'),
        os.path.join(base_dir, 'colon157_page_0002.png')]

filepaths = (os.path.join(base_dir, 'colon157.pdf'),
             os.path.join(base_dir, 'colon157_result.json'),
             pngs)
