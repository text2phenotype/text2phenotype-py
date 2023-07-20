import os

base_dir = os.path.dirname(__file__)

pngs = [os.path.join(base_dir, 'SKM_C335118053015010_page_0000.png'),
        os.path.join(base_dir, 'SKM_C335118053015010_page_0001.png'),
        os.path.join(base_dir, 'SKM_C335118053015010_page_0002.png'),
        os.path.join(base_dir, 'SKM_C335118053015010_page_0003.png'),
        os.path.join(base_dir, 'SKM_C335118053015010_page_0004.png'),
        os.path.join(base_dir, 'SKM_C335118053015010_page_0005.png')]

filepaths = (os.path.join(base_dir, 'SKM_C335118053015010.pdf'),
             os.path.join(base_dir, 'SKM_C335118053015010_result.json'),
             pngs)
