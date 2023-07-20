from datetime import datetime

from fhirclient.models.patient import Patient as FhirPatient
from fhirclient.models.fhirreference import FHIRReference as FhirReference
from fhirclient.models.contactpoint import ContactPoint
from fhirclient.models.humanname import HumanName
from fhirclient.models.identifier import Identifier
from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.medicationstatement import MedicationStatementDosage as FhirDosage
from fhirclient.models.medicationstatement import MedicationStatement as FhirMedicationStatement
from fhirclient.models.timing import Timing as FhirTiming
from fhirclient.models.timing import TimingRepeat as FhirTimingRepeat
from fhirclient.models.quantity import Quantity as FhirQuantity
from fhirclient.models.codeableconcept import CodeableConcept as FhirCodeableConcept

from text2phenotype.common import common


# FHIR Patient helper functions

def make_contact_point(system, use, value, prefer=False):
    contact = ContactPoint()

    contact.system = system
    contact.use = use
    contact.value = value

    if prefer: contact.rank = 1

    return contact


def make_fhirdate(dob):
    fdate = FHIRDate()
    fdate.origval = dob
    return fdate


def make_patient(dem):
    """
    make patient FHIR resource
    www.hl7.org/implement/Standards/fhir/patient.html

    :param dem: dict, (usually parsed from EMR record.)
    :return:
    """
    pat = FhirPatient()

    ident = Identifier()
    ident.use = 'secondary'
    ident.value = str(dem['id'])

    pat.identifier = [ident]

    fullname = HumanName()
    fullname.given = [dem['fname']]
    fullname.family = [dem['lname']]

    pat.name = [fullname]

    if dem.get('contact') is not None:
        pat.telecom = list()

        pat.telecom = [
            make_contact_point('email', 'home', dem.get('email'), common.fuzzy_word_match('email', dem['contact'])),
            make_contact_point('phone', 'home', dem.get('ph_home'),
                               common.fuzzy_word_match('home phone', dem['contact'])),
            make_contact_point('phone', 'mobile', dem.get('ph_cell'),
                               common.fuzzy_word_match('mobile phone', dem['contact'])),
        ]

    if dem.get('sex'):
        pat.gender = dem['sex'].lower()
    pat.birthDate = make_fhirdate(datetime.strftime(dem['dob'], '%Y-%m-%d'))

    # No address in most (all?) of the records we're getting. Leaving out for MVP SANDS-88
    # pat.address   = [make_address(zip5=dem.zip5, lines=[dem.addr1, dem.addr2])]

    return pat


def make_reference(ref: str) -> FhirReference:
    return FhirReference({'reference': ref})


def make_quantity(val: float, unit: str) -> FhirQuantity:
    q = FhirQuantity()
    q.value = val
    q.unit = unit
    return q


def make_timing(freq: float, unit: str) -> FhirTiming:
    t = FhirTiming()
    t.repeat = FhirTimingRepeat()
    t.repeat.frequency = freq
    t.repeat.periodUnit = unit
    return t


def make_dosage(dosage_value: float, dosage_unit: str, frequency_value: float, frequency_period: str) -> FhirDosage:
    d = FhirDosage()
    d.doseQuantity = make_quantity(dosage_value, dosage_unit)
    d.timing = make_timing(frequency_value, frequency_period)
    return d


def make_medication_statement(med_name: str, dosage_value: float, dosage_unit: str, frequency_value: float,
                              frequency_period: str, patient: str, date_asserted: datetime) -> FhirMedicationStatement:
    m = FhirMedicationStatement()
    m.status = 'active'
    m.taken = 'y'
    m.dateAsserted = make_fhirdate(date_asserted.strftime('%Y-%m-%d'))
    m.patient = make_reference(patient)
    m.medicationCodeableConcept = FhirCodeableConcept({'text': med_name})
    m.dosage = [make_dosage(dosage_value, dosage_unit, frequency_value, frequency_period)]
    return m
