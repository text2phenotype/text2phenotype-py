from text2phenotype.ccda import ccda


###############################################################################
#
# Get Summary (just like an NLP autocoded summary) from CCDA content
#
###############################################################################
def ccda2summary(ccda_xml):
    content = ccda.read_ccda_file(ccda_xml)
    summary = {'patientId': content.get('patientId'),
               'sex': content.get('sex'),
               'dob': content.get('dob')}

    if 'section' in content.keys():
        for section in content['section']:
            if 'template' in section.keys():

                template = section['template']

                # DO NOT include family history in personal summary
                if template['person'] is not None:
                    if template['person'] == 'Person.family':
                        continue

                # CCDA template summary
                aspect = template['aspect']
                aspect = str(aspect).replace('Aspect.', '').title()

                if 'codes' in section.keys() and len(section['codes']) > 0:
                    if aspect not in content.keys():
                        summary[aspect] = list()

                    for c in section['codes']:
                        summary[aspect].append(
                            {'text': c.get('displayName', 'no display name'),
                             'vocab': c.get('vocab', 'no vocab'),
                             'code': c.get('code', 'no code')})
    return summary
