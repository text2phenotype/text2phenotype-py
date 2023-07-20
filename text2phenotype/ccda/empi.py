"""
Enterprise Master Patient Index (patient matching)
"""
from lxml import etree
from dateutil.parser import parse
from text2phenotype.ccda import ccda
from text2phenotype.ccda import xpath
from text2phenotype.common.demographics import Demographics

# SEE https://gettext2phenotype.atlassian.net/browse/SANDS-222
PID_CERNER = '2.16.840.1.113883.1.13.99999.1'
PID_EMERGE = '2.16.840.1.113883.19.5.99999.2'
PID_OTHER = '2.16.840.1.113883.19'


def get_patient_data(ccda_xml: etree) -> dict:
    retval = {}
    root = etree.fromstring(ccda_xml)
    patient_role = root.find('patientRole') or etree.ElementBase()
    patient = patient_role.find('patient')
    if patient is None:
        return retval

    name_node = patient.find('name')
    if name_node is not None:
        retval['fname'] = get_text_from_element(name_node, 'given')
        retval['lname'] = get_text_from_element(name_node, 'family')

    gender_elems = xpath.findall_by_codeSystem(patient, ccda.Vocab.Gender.value)
    retval['sex'] = get_first(gender_elems, 'code') if len(gender_elems) > 0 else ''

    birth_elem = patient.find('birthTime')
    if birth_elem is not None:
        birthtime = birth_elem.attrib.get('value', '').split('.')[0]
        try:
            retval['dob'] = parse(birthtime).strftime('%Y-%m-%d')
        except ValueError:
            pass

    retval['race'] = get_race(patient)

    ssn_elements = xpath.findall_by_attribute(patient_role, 'root', ccda.Vocab.SSN.value)
    ssn = get_first(ssn_elements, 'extension')
    retval['ssn'] = ssn if ssn is not None else ''

    return retval


def get_first(element_list, attribute):
    if len(element_list) == 1:
        return element_list.pop().attrib[attribute]
    else:
        return None


def get_race(ccda_xml: etree) -> list:
    """
    Get raceCode and ethnicityGroupCode for patient
    :param ccda_xml:
    :return: list() of race ethnicity types for the patient
    """
    race = list()
    race_list = xpath.findall_by_codeSystem(ccda_xml, ccda.Vocab.RaceEthnicity.value)
    for el in race_list:
        if 'displayName' in el.attrib:
            race.append(el.attrib['displayName'])
    return race


def get_patient_id(ccda_xml, default=None):
    root = etree.fromstring(ccda_xml)
    ids = root.findall('patientRole/id')
    id_roots = [PID_CERNER, PID_EMERGE, PID_OTHER]
    patient_ids = [x.attrib['extension'] for x in ids if x.attrib['root'] in id_roots]
    if len(patient_ids) == 1:
        return patient_ids[0]
    elif default is None:
        raise ValueError("Could not determine the patient's Id value.")
    return default


def get_telecom(ccda_xml):
    root = etree.fromstring(ccda_xml)
    patient_role = root.find('patientRole')
    if not patient_role:
        return None

    telecoms = patient_role.findall('telecom')
    for tele in telecoms:
        if tele.attrib['use'] == 'HP':  # HP = home phone
            return tele.attrib['value']

    # in case nothing was found
    return None


def get_address(ccda_xml) -> dict:
    root = etree.fromstring(ccda_xml)
    patient_role = root.find('patientRole')
    if not patient_role:
        return dict()

    addresses = patient_role.findall('addr')
    for addr in addresses:
        if addr.attrib['use'] == 'HP':
            return {'addr1': get_text_from_element(addr, 'streetAddressLine'),
                    'city': get_text_from_element(addr, 'city'),
                    'state': get_text_from_element(addr, 'state'),
                    'zip5': get_text_from_element(addr, 'postalCode')}

    # in case nothing was found
    return dict()


def get_demographics(ccda_xml) -> Demographics:
    patient = get_patient_data(ccda_xml)
    patient_id = get_patient_id(ccda_xml, patient['ssn'])
    address = get_address(ccda_xml)
    telecom = get_telecom(ccda_xml)

    dem = Demographics(id=patient_id, phone_home=telecom, **patient, **address)
    return dem


def get_text_from_element(elem, search_tag):
    search_elem = elem.find(search_tag)
    if search_elem is not None:
        return search_elem.text
    else:
        return ''
