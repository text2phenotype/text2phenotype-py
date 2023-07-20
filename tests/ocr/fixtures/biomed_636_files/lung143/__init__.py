import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'lung143_page_0000.png'),
        os.path.join(base_dir, 'lung143_page_0001.png'),
        os.path.join(base_dir, 'lung143_page_0002.png'),
        os.path.join(base_dir, 'lung143_page_0003.png'),
        os.path.join(base_dir, 'lung143_page_0004.png')]

filepaths = (os.path.join(base_dir, 'lung143.pdf'),
             os.path.join(base_dir, 'lung143_result.json'),
             pngs)
