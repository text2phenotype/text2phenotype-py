from text2phenotype.constants.features import (
    DemographicEncounterLabel,
    PHILabel,
)


# script to transform demographics annotations to PHI annotations
# takes as input matched_annotated_demographics_anns

# Correct format for PHI ann is T1\tphi_label range[0] range[1]\t token

# DEMOGRAPHIC to PHI label dictionary name to name
DEM_to_PHI = {
    DemographicEncounterLabel.na: PHILabel.na,
    DemographicEncounterLabel.ssn: PHILabel.idnum,
    DemographicEncounterLabel.mrn: PHILabel.medicalrecord,
    DemographicEncounterLabel.pat_first: PHILabel.patient,
    DemographicEncounterLabel.pat_middle: PHILabel.patient,
    DemographicEncounterLabel.pat_last: PHILabel.patient,
    DemographicEncounterLabel.pat_phone: PHILabel.phone,
    DemographicEncounterLabel.pat_street: PHILabel.street,
    DemographicEncounterLabel.pat_city: PHILabel.city,
    DemographicEncounterLabel.pat_zip: PHILabel.zip,
    DemographicEncounterLabel.pat_state: PHILabel.state,
    DemographicEncounterLabel.pat_email: PHILabel.email,
    DemographicEncounterLabel.pat_initials: PHILabel.patient,
    DemographicEncounterLabel.pat_age: PHILabel.age,
    DemographicEncounterLabel.dr_first: PHILabel.doctor,
    DemographicEncounterLabel.dr_org: PHILabel.organization,
    DemographicEncounterLabel.dr_middle: PHILabel.doctor,
    DemographicEncounterLabel.dr_initials: PHILabel.doctor,
    DemographicEncounterLabel.sex: PHILabel.na,
    DemographicEncounterLabel.dr_id: PHILabel.doctor,
    DemographicEncounterLabel.dr_last: PHILabel.doctor,
    DemographicEncounterLabel.dr_phone: PHILabel.phone,
    DemographicEncounterLabel.dr_fax: PHILabel.fax,
    DemographicEncounterLabel.dr_street: PHILabel.street,
    DemographicEncounterLabel.dr_zip: PHILabel.zip,
    DemographicEncounterLabel.dr_city: PHILabel.city,
    DemographicEncounterLabel.dr_state: PHILabel.state,
    DemographicEncounterLabel.facility_name: PHILabel.hospital,
    DemographicEncounterLabel.insurance: PHILabel.healthplan,
    DemographicEncounterLabel.dr_email: PHILabel.email,
    DemographicEncounterLabel.dob: PHILabel.patient,
    DemographicEncounterLabel.race: PHILabel.na,
    DemographicEncounterLabel.ethnicity: PHILabel.na,
    DemographicEncounterLabel.language: PHILabel.na
}

