import unittest
import os
from text2phenotype.common import common


class TagTogBase(unittest.TestCase):
    BASE_DIR = os.path.join(os.path.dirname(__file__), 'tag_tog_sample_output')
    DIR_TO_HTML = 'plain.html'
    POOL = 'pool'
    SPECIFIC_FILES = ['aj7TDeRicOq1RkTN_W0ybYJHR1e0-text.plain.html',
                      'OpenEMR/avF1tGsmksRALVVmRcvd1oL8wuSi-david_vaughan.pdf.plain.html',
                      'OpenEMR/acPInTouQOC_eYqpL1pHMGolTdei-6_text2phenotype_smart.pdf.plain.html',
                      'OpenEMR/a9zIFuYOKAoe4oce9LYnEMq4vSfe-john_stevens.plain.html']
    TEXT_DIR = 'raw_text'
    ANN_DIR = 'ann.json/members/sfee'
    annotation_legend = common.read_json(os.path.join(BASE_DIR, 'annotations-legend.json'))


