import enum

from text2phenotype.constants.features import PHILabel


class DeidGroupings(enum.Enum):
    SAFE_HARBOR = {
        PHILabel.date, PHILabel.patient, PHILabel.username, PHILabel.bioid, PHILabel.idnum, PHILabel.email,
        PHILabel.street, PHILabel.city, PHILabel.state, PHILabel.country, PHILabel.zip, PHILabel.hospital,
        PHILabel.age, PHILabel.location_other, PHILabel.phone, PHILabel.url, PHILabel.fax, PHILabel.organization,
        PHILabel.profession, PHILabel.healthplan, PHILabel.device, PHILabel.doctor, PHILabel.medicalrecord}
    LDS_DATE = {
        PHILabel.patient, PHILabel.username, PHILabel.bioid, PHILabel.idnum, PHILabel.email,
        PHILabel.street, PHILabel.city, PHILabel.state, PHILabel.country, PHILabel.zip, PHILabel.hospital,
        PHILabel.age, PHILabel.location_other, PHILabel.phone, PHILabel.url, PHILabel.fax, PHILabel.organization,
        PHILabel.profession, PHILabel.healthplan, PHILabel.device, PHILabel.doctor, PHILabel.medicalrecord}
    LDS_DATE_PROVIDER = {
        PHILabel.patient, PHILabel.username, PHILabel.bioid, PHILabel.idnum, PHILabel.email,
        PHILabel.street, PHILabel.city, PHILabel.state, PHILabel.country, PHILabel.zip,
        PHILabel.age, PHILabel.location_other, PHILabel.phone, PHILabel.url, PHILabel.fax, PHILabel.organization,
        PHILabel.profession, PHILabel.healthplan, PHILabel.device, PHILabel.medicalrecord}
