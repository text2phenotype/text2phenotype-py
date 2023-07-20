import os
import re

from lxml import etree

from text2phenotype.ccda import blacklist, summarize, xpath
from text2phenotype.ccda.document import *
from text2phenotype.ccda.section import Section
from text2phenotype.ccda.vocab import Vocab
from text2phenotype.common import common
from text2phenotype.common.batchlog import BatchLog
from text2phenotype.common.errors import CCDAError
from text2phenotype.common.log import logger
from text2phenotype.constants.environment import Environment


###############################################################################
#
# CCDA Document level functions
#
###############################################################################

def parse(ccda_xml):
    """
    Parse CCDA XML File
    :param ccda_xml: fully qualified path
    :return: lxml root
    """
    return xpath.parse(ccda_xml)


def get_document_type(ccda_xml):
    """
    Get DocumentType for XML document
    :param ccda_xml: 'file' or '_ElementTree'
    :return: DocumentType
    """
    return DocumentType(xpath.find_template_code(parse(ccda_xml)))


def get_document_class(doc_type):
    """
    Get CCDA Document (CCD, DischargeSummary, etc) for a given doc_type
    :param doc_type: DocumentType
    :return: class of type text2phenotype.ccda.document.*
    """
    if not isinstance(doc_type, DocumentType):
        doc_type = DocumentType(doc_type)

    if doc_type == DocumentType.ccd:
        return CCD
    if doc_type == DocumentType.discharge_summary:
        return DischargeSummary
    if doc_type == DocumentType.progress_note:
        return ProgressNote
    if doc_type == DocumentType.consult_note:
        return ConsultNote
    if doc_type == DocumentType.history_and_physical_note:
        return HistoryAndPhysical
    if doc_type == DocumentType.diagnostic_imaging_study:
        return DiagnosticImagingStudy
    if doc_type == DocumentType.physician_discharge_summary:
        return PhysicianDischargeSummary
    if doc_type == DocumentType.surgical_operation_note:
        return SurgicalOperationNote
    if doc_type == DocumentType.procedure_note:
        return ProcedureNote


section_template_map = {entry.value.section: entry.value for entry in list(Section)}


###############################################################################
#
# Read CCDA (file --> json)
#
###############################################################################
def read_ccda_file(xml_file):
    """
    Read CCDA file and get json
    :param xml_file: XML file to parse
    :return: dict
        """

    # extract dob, sex, and patient id
    dob_str = None
    sex = None
    ids = []
    context = etree.iterparse(xml_file)
    for action, elem in context:
        if 'administrativeGenderCode' in elem.tag:
            sex = elem.attrib['code']
        elif 'birthTime' in elem.tag:
            dob_str = elem.attrib['value']
            if len(dob_str) == 14:  # includes HHMMSS time at the end of the date string
                dob_str = dob_str[:8]
        elif 'patientRole' in elem.tag:
            for e in elem.getchildren():
                search = re.search('({.*})(\w+)', str(e.tag))
                if search and len(search.groups()) == 2:
                    if search.groups()[1] == 'id' and e.attrib.get('extension'):
                        ids.append(e.attrib['extension'])

        # if we find an SSN-formatted id, use it, otherwise use the first id element we find
        patient_id = None
        for i in ids:
            if re.search('^\d{3}-\d{2}-\d{4}$', i):
                patient_id = i
                break
        if not patient_id and ids:
            patient_id = ids[0]

    root = parse(xml_file)

    doc_type = get_document_type(root)
    doc_class = get_document_class(doc_type)

    res = {'document': [doc_type.name, doc_type.value],
           'section': [],
           'patientId': patient_id,
           'sex': sex,
           'dob': dob_str}

    for section in list(doc_class):
        template = section_template_map.get(section.value)

        section_el = xpath.find_section(root, template.section)
        if section_el is not None:
            res_section = {'section': section, 'template': template.__dict__, }

            codes_found = xpath.findall_codes(root, template.section, template.vocab)
            codes_set = set()
            codes_list = []

            for element in codes_found:
                code = {x: y for x, y in element.attrib.items()}

                if 'code' in code.keys() and 'codeSystem' in code.keys():
                    vocab = Vocab(code['codeSystem'])
                    try:
                        code['vocab'] = vocab.name
                    except Exception as e:
                        logger.error(element.attrib)
                        logger.error(e)

                    if not blacklist.skip_code(vocab, code['code']):

                        # del clutter attributes
                        for clutter in ['{http://www.w3.org/2001/XMLSchema-instance}type', 'codeSystem',
                                        'codeSystemName']:
                            if clutter in code.keys():
                                del code[clutter]

                        if str(code) not in codes_set:
                            codes_set.add(str(code))
                            codes_list.append(code)

            res_section['title'] = xpath.find_title(section_el)
            res_section['codes'] = codes_list
            res_section['text'] = xpath.find_text(section_el)
            res_section['dump'] = dump_raw_text(section_el)

            res['section'].append(res_section)

    return res


###############################################################################
#
# Write CCDA html (file --> html)
#
###############################################################################

def write_ccda_html(xml_file, xsl_file, html_file):
    """
    Apply XSL transform to XML content to get an HTML output
    :param xml_file: CCDA
    :param xsl_file: CDA.xsl (or vendor specific implementation)
    :param html_file: output target file
    :return: str of HTML content that was written to file
    """
    logger.debug('xml= %s xsl= %s' % (xml_file, xsl_file))

    dom = etree.parse(xml_file)
    xslt = etree.parse(xsl_file)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)

    html_content = etree.tostring(newdom, pretty_print=True)

    with open(file=html_file, mode='wb') as bytes_file:
        bytes_file.write(html_content)

    return html_content


def write_ccda_summary_json(xml_file):
    """
    Write CCDA to JSON summary
    :param xml_file:
    :return: Dict/JSON summary
    """
    res = summarize.ccda2summary(xml_file)
    common.write_json(res, xml_file + '.summary.json')

    return res


###############################################################################
#
# process CCDA files in batch mode
#
###############################################################################

def process_ccda_file(xml_file, xsl_file=os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda', 'CDA.xsl')):
    """
    write JSON and HTML for XML input
    :param xml_file: CCDA file
    :param xsl_file: Stylesheet for writing html
    :return: None
    """
    # logger.debug('process_ccda_file ='+xml_file)

    write_ccda_html(xml_file, xsl_file, xml_file + '.html')
    write_ccda_summary_json(xml_file)

    common.write_json(
        read_ccda_file(xml_file),
        xml_file + '.json')


def process_ccda_dir(emr_dir, ccda_dir=os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda')):
    """
    process all ccda files in a directory

    :param emr_dir: directory root for EMR XML file(s)
    :param ccda_dir: ccda root directory
    :return: BatchLog
    """
    target_dir = ccda_dir + '/' + emr_dir
    batch = BatchLog(target_dir)

    for xml_file in common.get_file_list(target_dir, 'xml'):
        try:
            process_ccda_file(xml_file)
            batch.log_passed(xml_file)

        except Exception as e:
            batch.log_failed(xml_file, e)

    logger.info(batch.summary())

    return batch


###############################################################################
#
# CCDA Section Titles and Aspect Mappings
#
###############################################################################

def get_section_title_pretty(section, stopwords=['narrative', 'document', 'reported']):
    """
    Get a readable 'title' for the section heading, like 'medications on admission'
    :param section: section like
    :param stopwords: list of stopwords that should be removed from the title
    :return: human readable title of a CCDA section
    """
    title = []
    if '.' in section:
        doctype, section = section.split('.')

    for token in section.split('_'):
        if token not in stopwords:
            title.append(token)
    return ' '.join(title).strip().upper()


def get_section_aspect_map(ccda_dir='ccda'):
    """
    Read a directory of CCDA files and build a map of all known section headers into a 'human readable title'
    :param ccda_dir:
    :return: dict where key=title and value=aspect
    """
    import os

    mappings = dict()

    for section in Section:
        section_title = get_section_title_pretty(section.name)
        if section_title not in mappings:
            mappings[section_title] = str(section.value.aspect)

    for sample_dir in __ccda_samples__:
        for sample_file in common.get_file_list(os.path.join(ccda_dir, sample_dir), '.json'):
            res = common.read_json(sample_file)

            for entry in res['section']:

                aspect = entry['template']['aspect']
                title = entry['title'].strip().upper()
                section = entry['section']

                if title not in mappings:
                    mappings[title] = aspect
                else:
                    if mappings[title] != aspect:
                        raise CCDAError('Aspect collision (section)' + aspect + '!=' + mappings[title])

                section_title = get_section_title_pretty(section)

                if section_title not in mappings:
                    mappings[section_title] = aspect
                else:
                    if mappings[section_title] != aspect:
                        raise CCDAError('Aspect collision (section)' + aspect + '!=' + mappings[section_title])
    return mappings


###############################################################################
#
# CCDA samples
#
# https://bitbucket.org/gettext2phenotype/text2phenotype-samples/
#
###############################################################################

__ccda_samples__ = [
    'Allscripts/EnterpriseEHR',
    'Allscripts/InternalTest_MU2',
    'Allscripts/ProfessionalEHR',
    'Allscripts/SunriseClinicalManager',
    'Cerner',
    'EMERGE',
    'Greenway',
    'HL7',
    'Kareo',
    'Kinsights',
    'mTuitive_OpNote',
    'NextGen',
    'NIST',
    'Partners',
    'PracticeFusion',
    'TransitionsOfCare',
    'Vitera']


def process_ccda_samples(ccda_dir=os.path.join(Environment.TEXT2PHENOTYPE_SAMPLES_PATH.value, 'ccda')):
    """
    Process all CCDA samples
    :param ccda_dir: link to 'ccda' dir from https://bitbucket.org/gettext2phenotype/text2phenotype-samples/
    :return:
    """
    for sample in __ccda_samples__:
        process_ccda_dir(sample, ccda_dir)


###############################################################################
#
# XML Text
#
###############################################################################

def dump_raw_text(node):
    """
    Dump text from XML node tree (actual class is usually instance of Element)

    :param node: lxml.etree.Element
    :return: string of text raw dump of the XML content
    """
    res = []

    if isinstance(node, etree._Element):

        if node.text is not None:
            res.append(str(node.text))

        for child in node.getchildren():
            for nested in dump_raw_text(child):
                res.append(nested)
    else:
        print('type is ' + type(node))

    return list(filter(None, res))


def xml_string(node):
    return str(etree.tostring(node, pretty_print=True, method='text', encoding='unicode'))


###############################################################################
#
# Get LOINC codes
#
###############################################################################

def get_loinc_codes(ccda_xml):
    """
    Get LOINC codes for content in

    :param ccda_xml: XML content (or filepath)
    :return: dict() where {key=code  : val=displayName}
    """
    res = dict()

    doc_types = [entry.value for entry in list(DocumentType)]

    for code_el in xpath.findall_by_loinc(parse(ccda_xml)):

        attributes = code_el.attrib.keys()

        if {'code', 'displayName'} <= set(attributes):
            code = code_el.attrib['code'].strip()
            displayName = code_el.attrib['displayName'].strip()

            if code not in doc_types:
                if not blacklist.skip_section(code):
                    res[code] = displayName
    return res


def get_demographics_ccda(xml_file):
    """
    Read CCDA file and get json
    :param xml_file: XML file to parse
    :return: dict
        """

    # extract dob, sex, and patient id
    dob_str = None
    sex = None
    ids = set()
    pat_city = set()
    pat_street = set()
    pat_state = set()
    pat_zip = set()
    dr_city = set()
    dr_street = set()
    dr_state = set()
    dr_zip = set()
    pat_phone = set()
    race = set()
    pat_first = set()
    pat_last = set()
    ethnicity = set()
    facility_name = set()
    dr_phone = set()
    dr_fax = set()
    dr_first = set()
    dr_last = set()

    context = etree.iterparse(xml_file, events=['start'])
    for action, elem in context:
        if 'patient' in elem.tag:
            pat_info_elements = elem.getchildren()
            for child in pat_info_elements:
                if not isinstance(child.tag, str):
                    continue
                if 'addr' in child.tag:
                    address_elements = child.getchildren()
                    for addr in address_elements:
                        if not isinstance(addr.tag, str):
                            continue
                        if 'No' in get_elem_value(addr) and 'Indicated' in get_elem_value(addr):
                            continue
                        elif 'street' in addr.tag:
                            pat_street.add(get_elem_value(addr))
                        elif 'city' in addr.tag:
                            pat_city.add(get_elem_value(addr))
                        elif 'state' in addr.tag:
                            pat_state.add(get_elem_value(addr))
                        elif 'postalCode' in addr.tag:
                            pat_zip.add(get_elem_value(addr))
                elif 'telecom' in child.tag:
                    pat_phone.add(get_elem_value(child))
                elif 'name' in child.tag:
                    name_children = child.getchildren()
                    for name in name_children:
                        if not isinstance(name.tag, str):
                            continue
                        if 'given' in name.tag:
                            pat_first.add(get_elem_value(name))
                        elif 'family' in name.tag:
                            pat_last.add(get_elem_value(name))

        elif 'providerOrganization' in elem.tag:
            children = elem.getchildren()
            for child in children:
                if not isinstance(child.tag, str):
                    continue
                if 'name' in child.tag:
                    facility_name.add(get_elem_value(child))
                elif 'telecom' in child.tag:
                    dr_phone.add(get_elem_value(child))
                elif 'addr' in child.tag:
                    address_elements = child.getchildren()
                    for addr in address_elements:
                        if not isinstance(addr.tag, str):
                            continue
                        if 'No' in get_elem_value(addr) and 'Indicated' in get_elem_value(addr):
                            continue
                        elif 'street' in addr.tag:
                            dr_street.add(get_elem_value(addr))
                        elif 'city' in addr.tag:
                            dr_city.add(get_elem_value(addr))
                        elif 'state' in addr.tag:
                            dr_state.add(get_elem_value(addr))
                        elif 'postalCode' in addr.tag:
                            dr_zip.add(get_elem_value(addr))
        elif 'assigned' in elem.tag:
            children = elem.getchildren()
            for child in children:
                if not isinstance(child.tag, str):
                    continue
                if 'name' in child.tag:
                    if 'Person' in elem.tag:
                        names = child.getchildren()
                        for name in names:
                            if not isinstance(name.tag, str):
                                continue
                            if 'given' in name.tag:
                                dr_first.add(get_elem_value(name))
                            elif 'family' in name.tag:
                                dr_last.add(get_elem_value(name))
                    else:
                        facility_name.add(get_elem_value(child))

                elif 'telecom' in child.tag:
                    dr_phone.add(get_elem_value(child))
                elif 'addr' in child.tag:
                    address_elements = child.getchildren()
                    for addr in address_elements:
                        if not isinstance(addr.tag, str):
                            continue
                        if 'No' in get_elem_value(addr) and 'Indicated' in get_elem_value(addr):
                            continue
                        elif 'street' in addr.tag:
                            dr_street.add(get_elem_value(addr))
                        elif 'city' in addr.tag:
                            dr_city.add(get_elem_value(addr))
                        elif 'state' in addr.tag:
                            dr_state.add(get_elem_value(addr))
                        elif 'postalCode' in addr.tag:
                            dr_zip.add(get_elem_value(addr))

        elif 'administrativeGenderCode' in elem.tag:
            sex = elem.attrib['code']
        elif 'RaceCode' in elem.tag:
            race.add(elem.attrib['displayName'])

        elif 'ethnicGroupCode' in elem.tag:
            ethnicity.add(elem.attrib['displayName'])

        elif 'birthTime' in elem.tag:
            if len(elem.attrib['value'])>4:
                dob_str = elem.attrib['value']
                if len(dob_str) == 14:  # includes HHMMSS time at the end of the date string
                    dob_str = dob_str[:8]
        if 'patientRole' in elem.tag:
            for e in elem.getchildren():
                search = re.search('({.*})(\w+)', str(e.tag))
                if search and len(search.groups()) == 2:
                    if search.groups()[1] == 'id' and e.attrib.get('extension'):
                        ids.add(e.attrib['extension'])
                        ids.add(e.attrib['root'])

        # if we find an SSN-formatted id, use it, otherwise use the first id element we find
        patient_id = None
        for i in ids:
            if re.search('^\d{3}-\d{2}-\d{4}$', i):
                patient_id = i
                break


    res = {'pat_first': pat_first,
           'pat_last': pat_last,
           'pat_phone': pat_phone,
           'dob_str': dob_str,
           'sex':sex,
           'ids':ids,
           'pat_city':pat_city,
           'pat_state':pat_state,
           'pat_street': pat_street,
           'pat_zip': pat_zip,
           'dr_city': dr_city,
           'dr_state': dr_state,
           'dr_street': dr_street,
           'dr_zip': dr_zip,
           'race': race,
           'ethnicity': ethnicity,
           'facility_name':facility_name,
           'dr_first': dr_first,
           'dr_last': dr_last,
           'dr_fax': dr_fax,
           'dr_phone': dr_phone
    }
    return res


def get_elem_value(elem):
    if elem.get('value'):
        return elem.get('value')
    if elem.text:
        return elem.text
    return ''
