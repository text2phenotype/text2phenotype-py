from __future__ import absolute_import, unicode_literals

import lxml.etree as ET
from text2phenotype.ccda.vocab import Vocab

###############################################################################
#
# Parse XML
#
###############################################################################
def parse(ccda_xml):
    """
    https://stackoverflow.com/questions/18313818/how-to-not-load-the-comments-while-parsing-xml-in-lxml
    :param ccda_xml:
    :return:
    """
    # if ccda_xml is already parsed, return...
    if isinstance(ccda_xml, ET._ElementTree): return ccda_xml

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    return objectify.parse(ccda_xml, parser=parser)

###############################################################################
#
# Find CCDA Section Templates
#
###############################################################################
def findall_by_codeSystem(root, codeSystem):
    return list() if root is None else root.findall(".//*[@codeSystem='%s']" % codeSystem)

def findall_by_codeSystemName(root, codeSystemName):
    return list() if root is None else root.findall(".//*[@codeSystemName='%s']" % codeSystemName)

def find_by_codeSystem(root, codeSystemName):
    return root.find(".//*[@codeSystem='%s']" % codeSystemName)

def find_by_codeSystemName(root, codeSystemName):
    return root.find(".//*[@codeSystemName='%s']" % codeSystemName)

def findall_by_loinc(root):
    return findall_by_codeSystemName(root, 'LOINC')

def find_template_code(root):
    el = find_by_codeSystem(root, '2.16.840.1.113883.6.1')
    return None if el is None else el.attrib['code']

def find_section(root, section=None):
    _found = root.find("//*[@code='%s']" % section)
    return None if _found is None else _found.getparent()

###############################################################################
#
# findall codes
#
###############################################################################

def findall_codes(root, section, vocab=Vocab):
    if isinstance(vocab,   Vocab): vocab = vocab.value

    return findall_by_codeSystem(find_section(root, section), vocab)

###############################################################################
#
# text specific Xpath Functions
#
###############################################################################

def find_text_guard(node, simple, ns='{urn:hl7-org:v3}'):
    if node is not None:
        text = node.findtext(simple)
        return text if text is not None else node.findtext(ns+simple)

def find_text(node):
    return find_text_guard(node, 'text')

def find_paragraph(node):
    return find_text_guard(node, 'paragraph')

def find_title(node):
    return find_text_guard(node, 'title')

###############################################################################
#
# Other methods for accessing various locations in CCDA documents
#
###############################################################################

def findall_by_attribute(root, key, value):
    return list() if root is None else root.findall(".//*[@%s='%s']" % (key,value))
