import string
import unittest

from text2phenotype.common.common import chunk_text_by_size


class TestChunking(unittest.TestCase):
    
    def test_chunk_text_None_text(self):
        self.assertListEqual([], chunk_text_by_size(None, 50))

    def test_chunk_text_empty_text(self):
        self.assertListEqual([], chunk_text_by_size("", 50))

    def test_chunk_text_whitespace_text(self):
        text = string.whitespace
        self.assertListEqual([], chunk_text_by_size(text, 50))

    def test_chunks_text(self):
        text = TEST_TEXT

        chunks = chunk_text_by_size(text, 50000)

        self.assertEqual(len(chunks), 3)

        full_text_check = ''
        for chunk in chunks:
            text_range, text_check = chunk

            self.assertEqual(text_check, text[text_range[0]: text_range[1]])

            full_text_check += text_check

        self.assertEqual(full_text_check, text)


TEST_TEXT = """Note: Uploaded by patient, Steven Keating, after a brain tumor surgery (astrocytoma). This is the BWH legal medical record,
with doctor phone numbers and patient ID codes/details blanked out. If interested, more information on this case-specific
health data (imaging, labs, pathology, genetics, surgery video + more) is at www.stevenkeating.info
Thank you to the amazing medical teams for their great care and treatment, at BWH, DCFI, and MGH. Also thank you to
family/girlfriend/friends/MIT. Thanks and have a splendid day!
Partners HealthCare System, Inc.
Health Information Services Patient Extract MRN: (BWH)
BRIGHAM & WOMEN'S
HOSPITAL 

KEATING,STEVEN 
A Teaching Affiliate of Harvard From 1/1/2004 through 12/29/2014 Date of Birth: 04/29/1988
Medical School 75 Francis Street, 

: 26 yrs. Sex: M
Age
Boston, Massachusetts 02115
Table of Contents
.........
Cardiology 
Discharge Reports 

. . . . . . . . 2 
. . . . . . . . . . . . . . . 3 
...........................................
Endoscopy 

. No data is applicable
Infusion Flow Sheet
Laboratory 
Microbiology 
Neurophysiology 
Notes 
Operative Report 

............. 13
......... 18
...................................................... No data is applicable
...........................................................22
....................... 36
Pathology
Pulmonary 

......................................................... No data is 
applicable
Radiology
Vascular 
Printed: 12/29/2014 12:37 PM 

....... No data is applicable 
Page 1 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Cardiology From 1/1/2004 through 12/29/2014
08/15/2014 09:03 12 Lead ECG Final
Report Number: 2722171 
Type: 12 Lead ECG
Date: 08/15/2014 09:03
Ordering Provider: CHIOCCA, ENNIO

Report Status: Final
OOH
Reviewed by: LEWIS, M.D., ELDRIN F.

Ventricular Rate 60 BPM
Atrial Rate 60 BPM
P-R Interval 148 ms
QRS Duration 100 ms
QT 390 ms
QTC 390 ms
P Axis 48 degrees
R Axis 84 degrees
T Axis 49 degrees
Normal sinus rhythm
Normal ECG
No previous ECGS available
Confirmed by LEWIS, M.D., ELDRIN F. (225) on 8/19/2014 12:11:08 PM
Printed: 12/29/2014 12:37 PM 

Page 2 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports From 1/1/2004 through 12/29/2014
08/19/2014 06:22 Discharge Summary Final Ennio A. Chiocca, M.D. Ph.D.
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
Patient Information: 

Discharge Disposition: Home
Home address:
Patient/Family Agreed with discharge plan: Yes - 3
Contact Person: 
Name: 

Health Care Proxy:
Name :
Telephone:
Discharge Code Status: Full Code (presumed)
HOSPITAL CARE TEAM:
Service: NES Team: Unit-Bed:
Role: Name: Phone Number:
Inpatient Attending: 
Clinician contact at BWH: 
Discharging Clinician: 
Discharging Nurse: 
Care Coordinator: 
Occupational Therapist: 

CHIOCCA, ENNIO A.,M.D.,PH.D.
Chiocca, Ennio A
Meghan E. Dolan, P.A.-C.
Nina A Johnson, R.N.
Carol A Kale
Lisa R Cohen
OUTPATIENT CARE TEAM:
PCP: 

FIRN,LEIGH M.,M.D.
Diagnoses:
Admission: 
Principal Discharge: 
Discharge Condition: 

left frontal glioma
Intracranial glioma
Stable
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 1 of 10
Printed: 12/29/2014 12:37 PM 

Page 3 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
KEATING, STEVEN J
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical School
75 Francis Street, Boston, Massachusetts 02115
DOB: 04/29/1988 26M
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
TRANSITION PLAN:
Follow up Appointments:
Please call the numbers listed below to confirm that the appointments are scheduled for the locations listed. If you cannot
attend the appointments that have been scheduled for you, please call to reschedule them.
Chiocca, Ennio A, Neurosurgery
Address:
Phone:
Date/Time: 
Reason: 

8/ 29 / 2014 12:00:00 PM
Follow up admission 
Important Communication to Outpatient Care Providers
Results Pending at Discharge
Category Test(s) Date/Time Status
Pathology/Surgical 08/19/2014 In Process
Pathology
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 2 of 10
Printed: 12/29/2014 12:37 PM 

Page 4 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
ADMISSION PRESENTATION
Information obtained from LMR:
This is a 26-year-old right-handed white male who used to live in Canada. In 2007, he participated in a functional MRI
research study. At that time, he was called back saying that this was a lesion in his left frontal area. He was told that
this lesion could be followed because it was small. Over the years, he has had serial MRI scans, the last one in Canada
in October 2010 did not show growth of the lesion. He was then lost to follow up. However, in the last week, he
developed the equivalent of a seizure-like activity. This has involved lightheadedness, deja vu type feelings, smells, and
left eye twitching. He had no loss of consciousness. These episodes were followed by dull headaches. He was started
on keppra and then on MRI scan was performed. This showed a large left frontal and insular lesion. He comes in today
for followup. They obtained my name from a neurosurgeon that knows his PhD advisor. He otherwise has had no
speech issues. He had no memory issues.
FAMILY HISTORY: There is no family history of brain disease of brain cancer.
SOCIAL HISTORY: He does not use of tobacco. He is currently a PhD student and works on 3D printing. He
occasionally drinks. He is here not only with his PhD advisor, but also with his parents and other relatives.
PHYSICAL EXAMINATION: On examination, he is completely awake and alert. There are no focal neurological
symptoms or signs that I can tell.
IMAGING: His MRI scan shows a large left frontal and insular lesion that involves the operculum in the front where it
seems to be involving Broca's area. There is a little bit of the tumor in the left anterior temporal lobe as well. The tumor
is T2 and FLAIR hyperintense. It does put pressure with some left and right shift of the brain, particularly anteriorly.
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 3 of 10
Printed: 12/29/2014 12:37 PM 

Page 5 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
HOSPITALIZATION SUMMARY
Surgical (OR) Procedures:
08/19/14 CHIOCCA,ENNIO A.,M.D., PH.D.
BRAINLAB GUIDED AWAKE LEFT FRONTAL CRANIOTOMY FOR RESECTION OF BRAIN
TUMOR, HEAD HOLDER, MICROSCOPE, DRILL, BRAINLAB GUIDANCE, ANES:
M.A.C., ---ICU REQ--- (SCT 6:00 + 30)
Brief Summary Assessment:
Mr. Keating is a 26 year old male with a history of a left frontal low grade glioma and partial seizures s/p brainlab guided
awake left frontal craniotomy for resection of tumor with Dr. Chiocca on 8/19/14
Hospital Course:
Hospital Course: Patient was admitted to the Neurosurgical Service on 8/19/14 for a brainlab guided awake left frontal
craniotomy for resection of tumor with Dr. Chiocca. Patient was taken to the operating room on the day of admission
and underwent an uncomplicated procedure. Please see Dr. Chioccas's separately dictated operative note for details.
Post-operatively patient was extubated and transferred to the Neurosurgical ICU for close monitoring. He remained
hemodynamically stable, neurologically at baseline, and with his pain well-controlled throughout his hospital stay. On
POD#1 he was transferred to the floor in stable condition and was deemed ready for discharge on POD#2.
NEURO: Patient remained neurologically at baseline throughout his hospital stay. A&Ox3, PERRL, EOMI, VFF, FS,
TM, SAR 5/5, sensation grossly intact, no drift, steady gait. Post-op MRI of the brain was without complications. He was
maintained and discharged on Keppra 500 mg PO BID. He was started and discharged on a dexamethasone taper of 3
days to off.
CV: Hemodynamically stable at all times.
GU: Voiding on his own after foley removed with no signs of retention or UTI.
Gl: Tolerating a regular diet with no nausea or vomiting.
HEME: SQH and SCDs for DVT prophylaxis.
ID: Afebrile at all times. Perioperative ABX. Incision remained clean, dry, and intact with no evidence of erythema,
warmth, or hematoma.
DISPO: Ambulating on his own and feels ready to go home with no services needed. At the time of discharge his pain
remained well controlled on oral medications. Patient will follow up with Dr. Chiocca in 1-2 weeks.
Non-OR Procedures:
None
DISCHARGE EXAM
Discharge Vital Signs: 

Mental Status at Discharge : 
Alert, oriented, follows instructions
Date/Time Vital Signs Taken: 8/21/2014 12:00 PM
T: 35.8 degrees 
HR: 88 BPM 
BP: 120/64 mmHg 
RR: 20 per min 

Key Discharge Physical Exam Findings:
A&O x 3, PERRL, EOMI, VEF, FS, TM,
SAR 5/5, sensation grossly intact, no
drift, steady gait
02 Sat: 95 %
Current Weight: 75.5 kg Height/Length: 188 cm BMI: 21.4 

Pain Assessment : 
Intensity scale: 0
LABS AND STUDIES
Most Recent Reported BWH Lab Values During This Admission
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 4 of 10
Printed: 12/29/2014 12:37 PM 

Page 6 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
Basic Chemistry: Complete Blood Count: Routine Coagulation:
Na 137 8/21/2014 9:23 AM WBC 23.76 INR 1.1 8/21/2014 9:23 AM
8/21/2014 9:23 AM
K 3.8 8/21/2014 9:23 AM PTT 27.7 8/21/2014 9:23 AM
(H)
CI 98 8/21/2014 9:23 AM Hct 35.8 (L) 8/21/2014 9:23 AM
CO2 26 8/21/2014 9:23 AM Hbg 12.4 (L) 8/21/2014 9:23 AM
BUN 13 8/21/2014 9:23 AM PLT 259 8/21/2014 9:23 AM
Creat 0.73 8/21/2014 9:23 AM
Glu 131 8/21/2014 9:23 AM
Ca 9.3 8/21/2014 9:23 AM
Reference Ranges:
NA 136-145 mmol/L, K 3.4-5.0 mmol/L, CL 98-107 mmol/L, CO2 22-31 mmol/L, NA-PL 136-145 mmol/L, K-PL 3.4-5.0 mmol/L, BUN 6-23 mg/dL, CA 8.8-10.7
mg/dL, CRE 0.50-1.20 mg/dL, GLU 70-100 mg/dL, WBC 4-10 K/UL, HCT 40-54 %, HGB 13.5-18.0 g/dL, PLT 150-450 KuL, PT-INR 0.9-1.1, PTT 23.8-36.6
sec
* No result denotes that the lab test was not done during this patient's Hospitalization.
All labs performed at Brigham and Women's Hospital 75 Francis Street Boston, MA 02115
Most Recent BWH EKG Result During This Admission
Electrocardiogram Report (Accession # 15-09927K) REFERRED BY:CHIOCCA,ENNIO. REVIEWED BY:

LEWIS, M.D., ELDRIN F.
Date/Time: 08/15/14 09:03
VENT. RATE 60 BPM
PR INTERVAL 148 ms QRS DURATION 100 ms QTIQTC 390 390 ms P-R-T AXES 48 84 49
Normal ECG
No previous ECGs available
Confirmed by LEWIS, M.D., ELDRIN F. (225) on 8/19/2014 12:11:08 PM
REFERRED BY:CHIOCCA,ENNIO. REVIEWED BY: LEWIS, M.D., ELDRIN F.
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 5 of 10
Printed: 12/29/2014 12:37 PM 

Page 7 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical School
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
Instructions Given to Your Patient at Discharge:
Activities After Discharge:
Walking as tolerated
Other Activity Restriction - as per PT
Diet After Discharge:
House 8/21/2014 7:49:45 AM
Please resume all your home medications except blood thinners (aspirin, motrin, ibuprofen) unless otherwise instructed by
your surgeon. Please take pain medications only as needed for pain. Tylenol in addition to prescribed narcotics may help
for severe pain. Please do not drive, operate machinery, or drink alcohol while taking narcotic pain medications.
Please do not lift heavy weights (>20 lbs) for one month. No exercise or strenuous activity until after your follow-up
appointment.
Please call Dr. Chiocca's office to schedule your follow up appointment. You should be seen within 1-2 weeks for staple
removal.
If you need to reach Dr. Chiocca's office during normal business hours, M-F 8am-5pm, please call the phone number
below:
(617) 525-9419
If you are unable to reach someone at the above numbers or it is not during business hours please call:
617-732-5500, and have 17577 paged, the Neurosurgery resident on call.
Please do not get your incision wet until after sutures are removed at follow-up. It is OK to shower but keep incision dry.
Incision must be covered when showering, and the dressing or shower cap may be removed after showering.
Please call your MD immediately or go to the Emergency Department if the following symptoms occur: headaches, neck
pain, fever, chills, nausea, vomiting, diarrhea, worsening weakness, numbness, visual changes, chest pain, shortness of
breath, or any other symptoms of your concern.
Return to the Emergency Department or see your own doctor right away if
any problems develop, including the following:
--Fever >100.5 F or shaking chills.
--Purulent discharge (pus) from wound, or any increased drainage.
--Increased redness or swelling around the wound.
--Worsening Headache or Neck Stiffness.
--Seizures or any loss of consciousness, dizziness, or fainting.
--Blurry vision, double vision, or eye irritation.
--Nausea or vomiting.
--Chest or back pain, or shortness of breath.
PLEASE REMEMBER: It is OK to shower but do NOT get incision wet. Incision must be covered when showering and
dressing may be removed after showering. No driving while taking pain medication. Avoid strenuous activity until follow-up
appointment, at least. Call office or come to ER if: fever>100.5, increasing pain/headache, increasing nausealvomiting,
signs of wound infection (increasing pain, redness, warmth, swelling, or discharge), new or worsening neurologic deficit,
or anything else that is troubling to you. Staples will be removed in clinic.
Danger Signs:
Call your doctor if you have:
• Difficulty breathing or shortness of breath
• Chest pain or upper abdominal pain or pressure
• Fainting
• sudden dizziness
• weakness
• Severe headache
• Wound with redness or evidence of infection (drainage
• pus)
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 6 of 10
Printed: 12/29/2014 12:37 PM 

Page 8 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
• Any sudden or severe pain
• Severe persistent vomiting or diarrhea (three or more loose stools per day)
• Coughing or vomiting blood
• Suicidal Feelings
• Fever greater than 100.5 degrees Farenheit
• Difficulty speaking or walking
• Changes in vision or blurry vision
Confusion
Uncontrolled bleeding (e.g. does not stop bleeding when held for 10 minutes)
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 7 of 10
Printed: 12/29/2014 12:37 PM 

Page 9 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
MEDICATIONS
Allergies/Sensitivities:
Penicillins
Admission Medications:
1. ACETAMINOPHEN (TYLENOL) 500 MG PO Q8H
2. LEVETIRACETAM (KEPPRA) 500 MG PO BID
Discharge Medications
# Medication Name/ Dose / Frequency Medication Status*
DOCUSATE SODIUM
New Medication
100 mg by mouth two times a day
FAMOTIDINE
New Medication
20 mg by mouth two times a day
SENNOSIDES
New Medication
17.2 mg by mouth two times a day
ACETAMINOPHEN 
650 mg by mouth every 4 hours as needed FOR: Pain, Headache 

Changed Frequency and
Dose
DEXAMETHASONE
Taper by mouth 2 mg every 6 hours for 4 DOSES 

New Medication
1 mg every 6 hours for 4 DOSES
LEVETIRACETAM
500 mg by mouth every 12 hours 

Changed Frequency
Call HO for an IV order if patient is unable to take PO.
OXYCODONE
New Medication
5-10 mg by mouth every 4 hours as needed FOR: Pain, Headache
* Medication status indicates change from medication list before admission to medication list on discharge from hospital.
Immunizations Given During Inpatient Stay:
No H1N1, Seasonal Flu, Pneumovax or Diphtheria/Tetanus/Pertussis Vaccines were administered during this
admission.
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 8 of 10
Printed: 12/29/2014 12:37 PM 

Page 10 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
DISEASE MANAGEMENT:
Were the following conditions active problems during this hospitalization?
Heart Failure: No
Coronary Artery Disease: No
Ischemic Stroke/TIA: No
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 9 of 10
Printed: 12/29/2014 12:37 PM 

Page 11 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Discharge Reports from 1/1/2004 through 12/29/2014 (cont)
BWH BRIGHAM AND WOMEN'S HOSPITAL
A Teaching Affiliate of Harvard Medical Schoo
75 Francis Street, Boston, Massachusetts 02115
Admission: 8/19/2014
Discharge: 8/21/2014
Discharge Summary
FINAL
CC LIST:
PCP 

FIRN , LEIGH M . , M .D.
MIT MEDICAL 77 MASSACHUSETTS AVENUE,BUILDING E23
CAMBRIDGE, MA 02139
Follow Up Appointment 

Chiocca, Ennio A
Electronically signed by:
Name Role Date Time
Ennio A. Chiocca, M.D., Ph.D. Attending 8/28/2014 1:12 PM
Nina A Johnson, R.N. Nurse 8/21/2014 10:56 AM
Meghan E. Dolan,P.A.-C. Physician Assistant 8/21/2014 8:33 AM
Lisa R Cohen Occupational Therapist 8/21/2014 7:49 AM
Bichngoc Thi Nguyen,P.A.-C. Physician Assistant 8/20/2014 1:41 PM
Carol A Kale Nurse 8/20/2014 9:56 AM
Electronically signed by: Meghan E. Dolan,P.A.-C. on 8/21/2014 8:33:15 AM
Electronical 

d by : Nina A Johnson, R.N. on 8/21/2014 10:56:41 AM
Page 10 of 10
Printed: 12/29/2014 12:37 PM 

Page 12 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Laboratory From 1/1/2004 through 12/29/2014
CHEMISTRY
Date/Time NA K CL CO2 BUN CRE EGFR GLU
137 3.8 98 26 13 0.73 131(*)
08/21/2014
(136-145) 

(3. 4 - 5 . 0 
09:23 ) (98-107) (22-31) (6-23) (0.50-1.20)>=60(1) | (70-100)
(1)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
137
08/20/2014
(136-145)
16:50
134(*) 3.8 97(*) 24 13 0.78 150(*)
08/20/2014
(136-145) (3.4-5.0) (98-107) (22-31)
00:39 (6-23) (0.50-1.20)>=60(1)(70-100)
|(1)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
137 (#)(2) | 99 24 15 0.87 126(*)
08/19/2014 

3 . 6 
(136-145) 
18:10 (3.4-5.0) (98-107) (22-31) (6-23) (0.50-1.20)>=60(1)(70-100)
|(1)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
|(2)VERIFIED
19/2014 

168(*)
08/
(70-100)
16:17(1)
|(1)FI02: ART OR
138 4.9 100 25 15 0.86 181(*)
08/19/2014 
(136-145) (3.4-5.0) (98-107) (22-31) (6-23) (0.50-1.20)>=60(2)(70-100)
16:17(1)
(1)OR
|(2)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
158(*)
08/19/2014
(70-100)
12:50(1)
|(1)FIO2: ART,OR
134(*) 4.2 96(*) 27 14 0.93 161(*#)
08/19/2014
49(1)L(136-145) (3.4-5.0) (98-107) (22-31) (6-23) (0.50-1.20)>=60(2) | (70-100)
12:
(1)OR
|(2)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
138
08/15/2014 3.6 101 26 0.83 73
(136-145) (3.4-5.0) (98-107) (22-31) (6-23) (0.50-1.20)>=60(2) | (70-100)
11:39(1)
(1)surgery date 08/19/2014
(2)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
138 4.1 100 29 11 0.88 96
08/13/2014
(136-145) (3.4-5.0) (98-107) (22-31) (6-23) (0.50-1.20)>=60(1)(70-100)
12:52
|(1)(Abnormal if <60 mL/min/1.73m2
If patient is black, multiply by 1.21)
Date/Time ANION

13
08/21/2014
(5-17)
09:23
13
08/20/2014
08/2000/:392014 (5-17) L L L L
14
08/19/2014
(5-17)
18:10
Flag Key: * (Abnormal Value) # (Significant Change) C (Corrected)
Printed: 12/29/2014 12:37 PM 

Page 13 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Laboratory from 1/1/2004 through 12/29/2014 (cont)
13
08/19/2014
(5-17)
16:17(1)
(1)OR
11
08/19/2014 
(5-17)
12:49(1)
(1)OR
11
08/15/2014
(5-17)
11:39(1)
|(1)surgery date 08/19/2014
9
08/13/2014
(5-17)
12:52
Date/Time GLU-POC
164(*)
08/20/2014
(70-100)
11:11
150(*)
08/20/2014
(70-100)
06:01
Date/Timel CA IC L MG TBILI TP ALB| GLOB | OSM
9.3 

2.1(#)
08/21/2014
| 08/0921:/232014 (8.8–10.7) 

(1. 3 - 2 . 6 ) | 
9.2 1.6(*#) 285
08/20/2014
(8.8-10.7) (1.7-2.6) (278-297)
00:39
9.6 

2.1
08/19/2014
(8.8-10.7) 

(1.7-2.6)
18:10
2014 

1.14
08/19/
(1.13-1.32)
16:17(1)
(1)FIO2: ART OR
2014 9.3 2.0
08/19/
(8.8-10.7) 

(1.7-2.6)
16:17(1)
|(1)OR
1.15
08/19/2014
(1.13-1.32)
0902034
0412::50(1)
(1)FI02: ART,OR
9.3 

2.0
08/19/2014 
(8.8-10.7) 

(1.7-2.6)
12:49(1)
(1)OR
9.5 0.4 7.6 4.5 3.1
08/15/2014 
(8.8-10.7) (0.0-1.0) (6.4-8.3) (3.5-5.2)| (2.2-4.2)
11:39(1)
|(1)surgery date 08/19/2014
9.6
08/13/2014
(8.8-10.7)
12:52
Date/Timel bP02 bPCO2 bPH UBASEX 02 Sat NA-PL | K-PL CO2-PL
168(*#) 44 7.40 2 99.1(*) 28
08/19/2014
(65-95) (36-47) (7.35-7.45) (-3-3) (93.0-97.5) (22-30)
18:10(1)
(1)FIO2: ART
362(*) 50(*) 7.36 1 99.4(*) 138 4.9 29
08/19/2014 
(65-95) (36-47) (7.35-7.45) (93.0-97.5)(136-145) |(3.4-5.0)| (22-30)
16:17(1)
|(1)FI02: ART OR
Flag Key: * (Abnormal Value) # (Significant Change) C (Corrected)
Printed: 12/29/2014 12:37 PM 

Page 14 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Laboratory from 1/1/2004 through 12/29/2014 (cont)
99.6(*)
(93.0-97.5)
08/19/2014 365(*) 55(*) 7.37 4(*) 137 4.5 33(*)
(65-95) (36-47) (7.35-7.45) (-3-3) |(136-145)| (3.4-5.0) | (22-30)
12:50(1) 

99 . 2 ( * ) 
(93.0-97.5)
|(1)FIO2: ART,OR
Date/Time HGB BG 

HCT-BG
2014 14.1 41
08/19/
(13.5-18.0) 

(40-54)
18:10(1) 1 
(1)FIO2: ART
14.1 

41
08/19/2014 
(13.5-18.0) (40-54)

16:17(1)
(1)FI02: ART OR
14.9 

44
08/19/2014 
(13.5-18.0) (40-54)

12:50(1)
|(1)FI02: ART,OR
Date/Timel ALT/SGPT AST/SGOTI ALKP | TBILI
13 12 54 0.4
08/15/2014
(10-50) (10-50) (35-130)| (0.0-1.0)
11:39(1)
|(1)surgery date 08/19/2014
HEMATOLOGY
Date/Time WBC RBC HGB HCT MCy |MCH MCHC PLT
23.76(*) 4.04(*) T 12.4(*) 35.8(*) 88.6 30.7 34.6 259
08/21/2014
(4-10) (4.5-6.4) (13.5-18.0)| (40-54) (80-95) (27-32) (32-36)(150-450)
09:23
24.26(*) 4.18(*)| 13.1(*) 35.9(*) 85.9 31.3 36.5(*) 266
08/20/2014
(4-10) (4.5-6.4)(13.5-18.0)(40-54) (80-95) (27-32) (32-36)(150-450)
00:39
16.29(*#) 4.34(*) 13.2(*) 37.3(*) 85.9(#) 30.4 35.4(#) 282
08/19/2014
(4-10) (4.5-6.4)(13.5-18.0)(40-54) (80-95) (27-32) (32-36)(150-450)
18:10
9.67(#) 4.95 1 15.0 45.1 91.1 30.3 33.3 302
08/15/2014
(4-10) (4.5-6.4)(13.5-18.0)(40-54) (80-95) (27-32) (32-36)(150-450)
11:39(1)
|(1)surgery date 08/19/2014
6.26 4.85 14.9 43.1 88.9 30.7 34.6 299
08/13/2014
(4-10) (4.5-6.4) (13.5-18.0) (40-54) (80-95) (27-32) (32-36)(150-450)
12:52
Date/Timel 

RDW 
11.8
08/21/2014
(11.5-14.5)
09:23
11.7
08/20/2014
(11.5-14.5)
00:39
11.6
08/19/2014
18:10 

( 11 .5-14.5)
11.8
08/15/2014 
(11.5-14.5)
11:39(1)
|(1)surgery date 08/19/2014
11.7
08/13/2014
(11.5-14.5)
12:52
Date/Time %POLY-A%LYMPH-A%MONO-A%EOS-A 

%BASO-A
86.7(*) 4.8(*) 8.5(#) 0.0 0.0
08/21/2014
09:23 (48-76) (18-41) (4.0-11.0) (0-5) (0-1.5)
Flag Key: * (Abnormal Value) # (Significant Change) C (Corrected)
Printed: 12/29/2014 12:37 PM 

Page 15 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Laboratory from 1/1/2004 through 12/29/2014 (cont)
90.1(*) 4.3(*) 5.6(#) 0.0 0.0
08/20/2014
(48-76) (18-41) (4.0-11.0) (0-5) (0-1.5)
00:39
95.1(*#) 3.2(*#) 1.7(* ) 0.0 0.0
08/19/2014
(48-76) (18-41) (4.0-11.0) (0-5) (0-1.5)
18:10
63.0 26.1 9.4 1.2 0.3
08/15/2014
1) (48-76) (18-41) (4.0-11.0) (0-5) (0-1.5)
11:39(
|(1)surgery date 08/19/2014
53.2 37.4 7.3 1.6 0.5
08/13/2014
52L (48-76) (18-41) (4.0-11.0) (0-5) (0-1.5)
12:
Date/Time ANEUT-A ALYMP-A AMONO-A AEOSA- ABASO-A
20.59(*) 1.13 2.03(*) 0.00 0.01
08/21/2014
(1.9-7.6) 

(0.8-4.1) | (0.2-0.8) | (0-0.35)| (0.00-0.15)
09:23
21.83(*) 1.05 1.37(*) 0.00 0.01
08/20/2014
(1.9-7.6) (0.8-4.1) (0.2-0.8) (0-0.35)| (0.00-0.15)
00:39
15.49(*) 0.52(*) 0.28 0.00 0.00
08/19/2014
(1.9-7.6) (0.8-4.1) (0.2-0.8) (0-0.35) (0.00-0.15)
18:10
6.09 2.52 0.91(*) 0.12 0.03
08/15/2014
(1.9-7.6) (0.8-4.1) (0.2-0.8) (0-0.35) (0.00-0.15)
11:39(1)
|(1)surgery date 08/19/2014
3.33 2.34 0.46 0.10 0.03
08/13/2014
(1.9-7.6) (0.8-4.1) (0.2-0.8) (0-0.35) (0.00-0.15)
12:52
COAGULATION
Date/Time PT PT-INRI PTT
14.1 1.1 27.7
08/21/2014
(12.0-14.4)1(0.9-1.1) (23.8-36.6)

09:23
14.3 1.1 26.4
08/20/2014
00:39 (12.0-14.4) (0.9-1.1) (23.8-36.6)
14.0 1.1 23.8
08/19/2014
18:10 (12.0-14.4) (0.9-1.1)(23.8-36.6)
13.5 1.0 27.8
08/15/2014
(12.0-14.4). (0.9-1.1) (23.8-36.6)
11:39(1)
|(1)surgery date 08/19/2014
13.3 1.0 28.3
08/13/2014
12:52 (12.0-14.4) (0.9-1.1) (23.8-36.6)
URINALYSIS
Date/Time UA-COLOR UA-GLUC UA-BILI UA-KET | UR-SPGR | UA-BLD | UA-PH UA-PROT

NEG NEG NEG 1.006 NEG 6.5 NEG
08/15/2014
YELLOW(2) (0-0) (0-0) (0-0) (1.003-1.035) (0-0) (4.5-8.0) (0-0)
11:39(1)
|(1)surgery date 08/19/2014
(2)CLEAR
NEG NEG NEG 1.015 NEG 7.0 NEG
08/13/2014
YELLOW(1) (0-0) (0-0) (0-0) (1.003-1.035) (0-0) (4.5-8.0) (0-0)
12:52
|(1)CLEAR
Date/Time UA-UROBI 

UA - NITLEUK-EST
NEG NEG NEG
08/15/2014
(0-0) (0-0) (0-0)
11:39(1)
Flag Key: * (Abnormal Value) # (Significant Change) C (Corrected)
Printed: 12/29/2014 12:37 PM 

Page 16 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Laboratory from 1/1/2004 through 12/29/2014 (cont)
|(1)surgery date 08/19/2014
NEG NEG NEG
08/13/2014
(0-0) (0-0) (0-0)
12:52
Date/Time UAS-RBC UAS-WBC UAS-BACTUAS-SQHI OCAST HCAST UAS-CRYS UA-EPIS
NEG NEG NEG
08/15/2014
(0-3) (0-4) TR NEG (0-0) (0-2) NEG NEG
11:39(1)
|(1)surgery date 08/19/2014
Date/Time UAS-COM
08/15/2014
NEG
11:39(1)
|(1)surgery date 08/19/2014
BLOOD BANK
Date/Time 

BB Sp
08/15/2014
SEE DETAIL(1)
08:53
|(1)EXP: 08/18/2014 23:59
Date/Time ABO Rh | ABSCRN
08/15/2014 0

PositiveNegative
08:53
Date/Time ABO #2 

Rh #2
08/15/2014 
0 

Positive
08:53
Flag Key: * (Abnormal Value) # (Significant Change) C (Corrected)
Printed: 12/29/2014 12:37 PM 

Page 17 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Microbiology From 1/1/2004 through 12/29/2014
08/20/2014 02:26 RECTAL SWAB FOR VANCOMYCIN

RESISTANCE SCREENING
Specimen: 3482159 

Collected 19 - Aug - 14 18 : 00
Received 20-Aug-14 02:26
Ordering Provider:
Specimen Group: RECTAL
Specimen Type: RECTAL SWAB FOR VANCOMYCIN RESISTANCE SCREENING

VANCOMYCIN-RESISTANT ENTEROCOCCUS SCREEN (ADULTS)
Reported: 21-Aug-14
NO VANCOMYCIN-RESISTANT ENTEROCOCCI ISOLATED
Printed: 12/29/2014 12:37 PM 

Page 18 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Microbiology from 1/1/2004 through 12/29/2014 (cont)
08/20/2014 01:24 
Specimen: 3482127 

NARES FOR MRSA 
Collected 19 - Aug - 14 18 : 00
Received 20-Aug-14 01:24
Ordering Provider:
Specimen Group: NOSE/NASOPHARYNX
Specimen Type: NARES FOR MRSA

MRSA CULTURE (ADULTS)
Reported: 21-Aug-14
NO METHICILLIN-RESISTANT STAPHYLOCOCCUS AUREUS ISOLATED
Printed: 12/29/2014 12:37 PM 

Page 19 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Microbiology from 1/1/2004 through 12/29/2014 (cont)
08/15/2014 10:13 
Specimen: 3480190 

URINE 
Collected 15 - Aug - 14 08 : 53
Received 15-Aug-14 10:13
Ordering Provider: CHIOCCA, ENNIO A. Dr. M.D.
Specimen Group: URINE
Specimen Type: URINE

Specimen Comment: surgery date 08/19/2014
AEROBIC CULTURE, URINE
Reported: 17-Aug-14
NO GROWTH
Printed: 12/29/2014 12:37 PM 

Page 20 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Microbiology from 1/1/2004 through 12/29/2014 (cont)
08/13/2014 13:38 
Specimen: 3479163 

URINE 
Collected 13 - Aug - 14 12 : 12
Received 13-Aug-14 13:38
Ordering Provider: TRIGGS, DANIEL VENANCE N.P.
Specimen Group: URINE
Specimen Type: URINE

AEROBIC CULTURE, URINE
Reported: 14-Aug-14
Total Colony Count 1,000
MIXED FLORA (3 OR MORE COLONY TYPES)
Printed: 12/29/2014 12:37 PM 

Page 21 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes From 1/1/2004 through 12/29/2014
10/07/2014 Neuropsychological Evaluation Final Humphreys, Clare T., Ph.D.
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
Dana-Farber Cancer Institute
Division of Medical Oncology
Brigham and Women's Hospital
Division of Cognitive & Behavioral Neurology & Neuropsychology
--------------------------------------------------------------------
NEUROPSYCHOLOGICAL EVALUATION
Keating, Steven
BWH #
DOB 4/29/88
DOE 10/7/14
Identifying information/reason for referral: Steven Keating is 26-year-old R-handed man with newly diagnosed left frontal diffuse
astrocytoma who presents for evaluation of cognitive functioning. He was referred by Dr. Patrick Wen in light of medical history
and to establish a cognitive baseline. Today's evaluation consisted of a review of available medical records, a clinical interview,
and the completion of a battery of neuropsychological tests. There is no history of prior neuropsychological testing. All
background information was obtained from the patient or from the longitudinal medical record (LMR).
History of presenting concerns: Medical history is well documented in LMR and in Dr. Wen’s recent notes, which I have
reviewed. In brief summary, Mr. Keating was a voluntary participant in an fMRI research study in December 2007, and was
notified that there was an abnormality on his scan. A brain MRI was obtained, which demonstrated a small left inferior frontal
T2/FLAIR hyperintensity felt to be possibly consistent with cortical dysplasia or low grade glial neoplasm. A follow-up scan in
several years was recommended. He had a repeat brain MRI in 2010 and was told that the lesion was stable. He was then in his
usual state of health until about one year ago, when he began to notice severe headaches after vigorous exercise. Starting in mid
June 2014, he began to experience frequent stereotyped episodes of 20 seconds of light-headedness and a feeling of "questioning
my own reality," followed by about a minute of smelling a strong acidic smell, light-headedness and L>R eyelid twitching without
convulsive movements or loss of consciousness. These spells occurred every few days, with as many as three spells in one day,
and were followed by a dull headache for about 20 minutes. He presented to a neurologist for evaluation and was started on
Keppra 250mg BID and referred for MRI of the brain, which demonstrated a large non-enhancing left frontal mass lesion. He
underwent resection of this lesion on August 19, 2014 (Dr. Ennio Chiocca) with pathology consistent with a diffuse astrocytoma,
WHO Grade II, and is now followed by Dr. Wen (DFCI Neuro-oncology) for treatment planning. On interview today, he
reported that his primary concerns post-surgically have been significant insomnia and increased anxiety. With respect to sleep, he
has difficulty primarily with maintenance, awakening for periods of 30-60 minutes in the early morning hours. This has improved
slightly but remains problematic. In addition, he reported the onset of understandable anxiety symptoms since his diagnosis, which
include thoughts running through his head, vigilance regarding physical symptoms (e.g. those that might be related to his tumor),
and a sense of inability to “trust” his own mind due to his experience of olfactory hallucinations in the past. He finds that he does
relatively well when distracted or around others, but experiences more acute anxiety during the nighttime hours or when alone. He
denied symptoms of depression, describing his mood as “contemplative rather than sad. When questioned regarding cognitive
domains, he generally denied post-surgical changes in functioning. The sold areas endorsed included mild inattention (which he
attributes to his ongoing anxiety and degree of preoccupation) and a slight increase in typographical errors, which has led him to
check his emails more carefully. He noted that he experienced some paraphasic errors immediately after surgery, but this resolved
within days.
All aspects of ADLs are intact. He has good medication adherence and uses a pill organizer. He does not have a car and uses
public transportation. He used a bicycle in the past and always wears a helmet. He is managing his finances with no difficulty. He
is making efforts to exercise daily and has noted some benefit in terms of his sleep. He reported good social and family support.
Oncology History
• December 2007: small left inferior frontal T2/FLAIR hyperintensity found incidentally on fMRI study
Page 1 of 9
Printed: 12/29/2014 12:37 PM 

Page 22 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
• 2010: follow up MRI with stable lesion
• Spring/summer 2013: began to notice severe headaches after vigorous exercise
• July 2014: presented to neurologist for evaluation of 6 week history of stereotyped episodes of acidic smell, derealization,
light-headedness and L>R eyelid twitching. MR brain obtained, demonstrating large primarily non-enhancing left frontal
mass lesion
• 8/19/14: underwent resection of L frontal tumor (Dr. Ennio Chiocca). Path: Diffuse Astrocytoma, WHO Grade II
Additional Medical History: Unremarkable. He had a loss of consciousness in high school while engaged in a breath-holding
context and chipped a tooth, but has no concussion history. No seizure symptoms post-surgically although he occasionally has
mild “aura-like” symptoms.
Neuroimaging/Prior Studies: Recent MRI available in LMR; Postsurgical changes with a resection cavity in the left frontal lobe,
with regions of T2 abnormality medial and posterior to the cavity. Mild linear enhancement along cavity most likely postsurgical.
No evidence of enhancing, hypervascular or hypercellular tumor progression.
Psychiatric History: There is no history of psychiatric diagnosis or treatment, no history of psychotropic medication trials, and no
history of participation in psychotherapy.
Relevant Family History:
History of Meniere's disease in his mother, as well as migraines and a question of bipolar disorder (due to what may have been a
single manic episode as well as depressive episodes per description).
Current Medications:
Keppra (LEVETIRACETAM) 500MG TABLET Take 1 Tablet(s) PO BID
Tylenol Extra Strength (ACETAMINOPHEN Extra Strength) 500 MG TABLET as directed, as needed
Melatonin
Valerian
Omega 3 supplement
Social History: Mr. Keating was born and raised in Calgary, Canada and currently lives with roommates while attending MIT.
He has been in a relationship with his girlfriend for seven months, and described this as a significant source of support. He has not
used caffeine since his surgery, and drinks alcohol occasionally (once per week at maximum). He does not use any other
substances.
Educational/Occupational History: Early development was unremarkable to the best of his knowledge. He was generally an
excellent student who earned A grades and graduated at the top of his high school class. He went on to complete a bachelor's
degree in Mechanical Engineering and Film at Queen's University. He is currently in his fifth year of graduate study at MIT, with
all coursework completed. He is considering whether to delay his thesis work due to his diagnosis and potential need for
treatment. His performance has been excellent throughout grad school, with a GPA of 4.9. He holds a research assistant position
at MIT, and is otherwise a full time student.
Relevant Review of Systems:
Sleep: Bedtime 11pm-12am, uses computer in bed with light filter. Sleep onset within 15-20 minutes. Awakening between 3-4
am for 30-60 minutes, again at 6 am. Using blackout blinds. No snoring or abnormal movement reported. Possible increased
urination at night which may contribute.
Appetite/Weight: Recent 5 pound weight loss, eating a healthy diet.
Sensory functioning: Increased sensitivity to sound and decreased olfactory acuity post-surgically. Scalp numbness, cold hands
and feet.
Page 2 of 9
Printed: 12/29/2014 12:37 PM 

Page 23 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Visit Date: 10/07/2014
Author: Electronically Signed by Clare T. Humphreys, Ph.D.
Motor functioning: No changes in gait, balance, or coordination. No tremor.
Headache: Occasional, possibly associated with dehydration. Endorsed related anxiety/vigilance
Nausea: Denies
Pain: Denies
MENTAL STATUS EXAMINATION
Appearance: Well dressed, well groomed, arrived on time and unaccompanied for appointment.
Behavior: Pleasant and cooperative. Social graces and comportment were intact. Rapport was readily established.
Speech: Fluent and normal in rate, volume, and tone.
Motor (strength, tone, gait and abnormal movements): No abnormalities noted. Patient ambulated independently between waiting
area and exam room. Gross and fine motor control were intact
Mood: “contemplative”
Affect: Full range, congruent with mood and topics discussed
Thought process: Logical and goal directed; excellent personal historian
Thought content: Appropriate to topic
Insight Good
Judgment: Intact
Cognitive Exam (orientation, memory, attention, language, fund of knowledge): Fully oriented to date and location. Easily
registered 3/3 words at first attempt, and recalled 3/3 after brief distraction. Serial seven subtractions were performed efficiently
and without error. Naming, repetition, comprehension, and basic reading and writing skills were intact. Verbal fluency was above
average for phonemic and semantic trials. Visual construction skills were intact on figure copy tasks (intersecting pentagons and
wire cube) and clock drawing was within normal limits. There was no evidence of visual or perceptual difficulties on screening.
10 minute delayed recall for a name and address was 5/7, and improved to 7/7 with multiple choice cues. MMSE = 30/30;
ACE-R = 97/100
Suicidal ideation: [x] no clinical indicators to suggest
[x] denies [ ] present (explain intent, plan, access to means)
Homicidal Ideation: [ X ] no clinical indicators to suggest
[ ] denies [ ] present (explain intent, specificity of target, access to means
Multi-axial Diagnosis
Axis I: 294.9 Cognitive Disorder NOS
Axis II: Deferred
Axis III: Brain tumor
Axis IV: Moderate (Medical and academic stressors)
Axis V (GAF) Current: 75
Recommendation/plan: As a result of this diagnostic evaluation, it is recommended that Mr. Keating proceed to
neuropsychological testing to include a comprehensive battery of tests of cognitive function, mood, and personality. He
understands and is in agreement with this plan. He is motivated and fully capable of participating in the evaluation process.
Neuropsychological Testing (Initial): the examination consisted of record review, testing, scoring, interpretation, integration and report writing
by psychologist [96118: 5 hours; Addenbrooke's Cognitive Examination-Revised: Attention & Orientation, Memory, Fluency, Language, and
Visu ospatial subscales) and selected testing and scoring by technician-Sara Rushia, B.A. [96119: 3 hours; Test of Premorbid Functioning
(TOPF), Wechsler Adult Intelligence Scale-IV (WAIS-IV: Similarities, Digit Span, Digit Symbol-Coding, Matrix Reasoning), Wechsler
Memory Scale-IV (WMS-IV: Logical Memory, Visual Reproduction), California Verbal Learning Test-II, Rey-Osterreith Complex Figure test,
Delis-Kaplan Executive Function System (DKEFS Verbal Fluency, Trail Making, Color-Word, Tower), Conners' Continuous Performance Test
II, Boston Naming Test, Narrative Writing Sample, Grooved Pegboard, Beck Depression Inventory-II, Beck Anxiety Inventory]
Behavioral Observations during Testing:
Mr. Keating was alert, engaged, and easily established rapport with the examiners. He expressed interest in the testing process
and was highly motivated. Comprehension was intact for all task instructions and he worked independently without need for
Page 3 of 9
Printed: 12/29/2014 12:37 PM 

Page 24 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
prompting or redirection. He asked appropriate questions about the tasks when he required additional clarity. He occasionally
provided more complex responses than required on less structured tasks. He showed an appropriate range of emotional
expression and intact frustration tolerance. He occasionally appeared disappointed in his performance or mild anxious, but this
did not significantly affect his ability to engage in the presented tasks. He was slightly restless at times (e.g. shifting in his seat) and
showed some evidence of fatigue (yawning, mild inattention) toward the end of the lengthy testing session. However, he
continued to put forth excellent effort and the presented results can be considered a valid estimate of his current cognitive
functioning.
Summary of Test Results (please also see attached table):
Baseline intellectual functioning was estimated to fall within the superior range, and performance on selected verbal and visual
intellectual tasks were superior and consistent with this estimate. Specific subtest performances are discussed further below.
Basic auditory attention and working memory were consistently within the average range, with spans of 7 digits repeated, 5 digits
backward, and 6 digits (variably) sequenced. This represents a mild weakness relative to Mr. Keating's superior level of
intellectual functioning. Processing speed on a digit-symbol coding task with demands on divided visual attention and working
memory was high average. Speed was superior on paper-and-pencil tasks of visual scanning and number and letter sequencing,
and speed remained above average when cognitive set-shifting demands were introduced (letter-number sequencing). All of the
above tasks were performed without error. Activation and sustained retrieval were superior and very superior (respectively) on
timed verbal fluency tasks requiring generation of words in response to phonemic (first letter) and semantic (category) prompts.
When cognitive flexibility demands were increased (generation of responses from alternating semantic categories), speed of
generation remained in the superior range. He made a slightly elevated number of repetition errors, but this was in the context of a
very high number of total responses. Verbally-mediated processing speed on timed word reading and color naming tasks was
average to high average. Speed remained high average when response inhibition demands were introduced (color-word
condition) on a subsequent inhibition/set-shifting condition. Accuracy was also above average with 0 errors across conditions.
On an extended task requiring attention, sustained concentration, vigilance, and response inhibition performance was within
normal limits, with faster than average response times, low error rate, and intact ability to adapt to changes in task demand. The
sole area of weakness was mild loss of response consistency as the task progressed over time, but the overall results were within
the non-clinical range, without indication of clinically significant attentional problems.
Performance on a problem-solving task requiring spatial planning, rule learning, and maintenance of cognitive set (Tower task)
was above average. All items were completed correctly and within the time allowed, and the majority were completed within or
near the optimal number of moves. Mr. Keating correctly recognized when an error led to the need for a higher number or moves
to complete a trial, and expressed some disappointment in his performance. However, his overall score was above average and
completion speed and accuracy were well within normal limits. Abstract verbal reasoning was in the superior range, as was
performance on a visual abstract reasoning task requiring completion of increasingly complex patterns.
Learning and memory performances were generally high average to superior. On a list learning task, initial encoding of a 16-word
list was average at the first of five learning trials with an intact learning curve and superior encoding for learning trials 1-5. After
presentation of a distracter list, recall remained superior at 15/16 words, while learning of the distracter list (which is presented
only once) was average at 6/16. After a 20-minute distraction filled delay, recall for the original list was high average (14/16), and
improved to 15/16 with category cues. Recognition discrimination was intact (high average range) and error free. Recall for
contextual verbal material (detailed short stories) was high average immediately following presentation and remained high average
after 25-minute delay, 100% retention over time. Recognition discrimination for story details was intact within normal limits.
Visual memory for briefly presented geometric designs was high average immediately following presentation, and superior after
25-minute delay with 98% percent retention over time. Recognition discrimination was error-free. Incidental recall of a
previously copied complex figure was average after brief distraction, and remained average after 20-minute delay, with 100%
retention. Mr. Keating showed good recall of the overall figure gestalt and major components, with some loss of internal detail at
the level of initial encoding. However, as shown by his percent retention, information storage over time was entirely intact.
Language was entirely within normal limits with regard to comprehension, repetition, and word reading. Narrative writing was
legible, well-composed, free from errors, and accurately described character roles and other relevant aspects of a visual scene.
Performance on a confrontation naming task was within normal limits.
Page 4 of 9
Printed: 12/29/2014 12:37 PM 

Page 25 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
Visuospatial functions were entirely intact. There was no evidence of difficulty with visual perception, and visual construction on a
complex figure copy task was in the superior range. He produced a highly precise and error-free copy. As mentioned above,
performance on a visual pattern completion task was also in the superior range.
Fine motor speed and dexterity were high average bilaterally, with a typical dominant hand advantage. Basic graphomotor speed
on a line tracing task (dominant hand) was in the superior range.
Responses to self-report inventories indicated minimal depressive symptoms, and fell below the cut-off for symptoms of worry
typically associated with generalized anxiety.
Impressions and Recommendations: In summary, Mr. Keating is a 26-year-old man with a history of recently diagnosed left
frontal astrocytoma referred for evaluation by his neuro-oncologist. Results of today's evaluation describe him as a man of
superior estimated premorbid functioning who demonstrates mild relative weaknesses in attention and working memory. A very
mild was also noted in single-trial learning and initial encoding of information with high organizational demands, which is likely
reciprocally related to attentional functioning. However, it is important to emphasize that these scores were still within normal
limits for age and education, and represent areas of weakness only in relation to superior range functioning in other areas. Mr.
Keating's cognitive profile is primarily one of strengths, with above average to superior scores across domains and across most
administered tasks today, consistent with his estimated premorbid abilities. He has also demonstrated considerable emotional
resilience in response to this significant health challenge. He is experiencing understandable anxiety that appears to be
circumstantial/situational rather than representing a primary anxiety disorder. However, these symptoms are causing him distress
and potentially interfering with sleep. In terms of etiology of mild cognitive weaknesses, anxiety symptoms are likely to be
contributory, and weaknesses in attention and working memory can also be associated with disrupted sleep. In addition, his
frontally located tumor and associated disruption of frontal-subcortical networks may be contributory as well. Again, however,
these weaknesses were mild in nature and occur in the context of multiple areas of cognitive strength, suggesting that Mr. Keating
is functioning at or near his baseline level. He is motivated to address and improve his anxiety symptoms and sleep, and this will
likely have a beneficial impact on attention and concentration in daily life. The following recommendations are provided:
1) There are several available DFCI resources that may be extremely helpful to Mr. Keating. Consultation with
psychosocial oncology is a recommended initial first step, for additional evaluation of and input regarding anxiety
symptoms. Mr. Keating indicated a preference for non-pharmacological treatments today, and a referral to the Young
Adult Program (http://dana-farber-yap.org/) and Karen Fasciano, PsyD, is also recommended. Mr. Keating is insightful
and motivated and will be an excellent candidate for cognitive-behavioral treatment of anxiety symptoms, as well as
benefitting from additional support and normalization of his experience. Complementary approaches to stress
management may also be a useful addition to Mr. Keating's treatment. Services in this area are available through the
olan
DFCI Zakim Center 

). Mindfulness- based meditation and stress reduction practices are also 
recommended. In addition to benefits for stress and anxiety, these techniques have also been associated with
improvement in aspects of cognitive function such as attention and working memory. Recommended resources include
the UMass Medical School Center for Mindfulness website (www.umassmed.edu/cfm), “Mindfulness for Beginners by
Jon Kabat Zinn, and the book “The Mindful Way Through Anxiety' by Orsillo and Roemer.
2) Continued work to improve and consolidate sleep will be helpful for mood and cognition. Mr. Keating was
encouraged to try a week-long behavioral experiment and eliminate computer use in bed. He will also continue to benefit
from daily physical exercise and the use of good environmental sleep strategies (which he has implemented
independently). If insomnia symptoms do not improve, he may also wish to consider beginning a bed time relation
routine. This can take many forms and he should determine which is the best fit for him. Approaches include mediation,
using a guided imagery or relaxation protocol (for example, see free downloads available through MITMedical at
http://medweb.mit.edu/wellness/resources/downloads.html), and using a journal to write and record worries, tasks, and
other aspects of the day that may be interfering with relaxation. “Externalizing these factors by acknowledging and
writing them down can help to calm anxious thoughts. For additional strategies, resources such as “The Insomnia
Workbook" by Stephanie Silberman can be helpful. In addition, there are psychologists with specialized expertise in
cognitive behavioral treatment of insomnia, including Lisa Strauss, PhD ( 
Dana-Farber also offers the “Sleep 8 Feel Great program beginning in January. Call 

and Claudia Toth, PsyD (
, or
Page 5 of 9
Printed: 12/29/2014 12:37 PM 

Page 26 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
emaildfci_adultsurvivors@dfci.harvard.edu for more information or to register.
3) Today's results will serve as a helpful cognitive baseline, and I would like to see Mr. Keating in 12 months for
updated evaluation. This will allow for assessment of any interval change and provision of updated recommendations.
It was a pleasure to meet and work with this very bright and resilient man. I appreciate the opportunity to participate in his care.
Please do not hesitate to contact me at 

with any questions regarding this report or the accompanying
recommendations.
Clare Humphreys, Ph.D.
Clinical Neuropsychologist
Dana-Farber Cancer Institute
Division of Medical Oncology
Brigham and Women's Hospital
Division of Cognitive & Behavioral Neurology
Name|Steven Keating
MRN
DOB 
DOE 
Age 
Edu 
Hand 
Sex 

04 / 29 / 88 
10 / 07 / 14 
26 
20 
Right 
Male 
NEUROPSYCHOLOGICAL EXAMINATION Raw z I SS % Classification
INTELLECTUAL ABILITY
Wechsler Adult Intelligence Scale - 4th ed. (WAIS-IV)
Verbal Comprehension
Similarities 311.33 14 91Superior
Perceptual Reasoning
Matrix Reasoning 241.67 15 95Superior
Working Memory
Digit Span 27-0.33 9 37Average
Processing Speed
Coding 840.67 High Average
ESTIMATED PREMORBID INTELLIGENCE
Test of Premorbid Functioning 500.60 Average
COGNITIVE SCREEN
Mini Mental Status Exam (MMSE) 301.11 61117 86 High Average
ACE-R (Scored as Age 50)
Total (1100) 
Attention and Orientation (118) 
Memory (126) 
Fluency (114) 
Language (726) 
Visuospatial (116) 

Points Above Cutoff 
Points Above Cutoff 
Points Above Cutoff 
Points Above Cutoff 
Points Above Cutoff 
Points Above Cutoff 
Page 6 of 9
Printed: 12/29/2014 12:37 PM 

Page 27 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
| EXECUTIVE FUNCTIONS
Wechsler Adult Intelligence Scale - 4th ed. (WAIS-IV)
Digit Span Forward 10 -0.33 9 37Average
Digit Span Backward 8 -0.33 9 37 Average
Digit Span Sequencing 0.00 50 Average
Longest Digit Forward
Longest Digit Backward
Longest Digit Sequence
Delis-Kaplan Executive Function System (D-KEFS)
Trail Making Test
Visual Scanning 111.33 14 91Superior
Number Sequencing 151.33 14 91Superior
Letter Sequencing 1.33 14 91Superior
Number-Letter Switching 0.67 75High Average
Motor Speed 101.33 91Superior
Total Switching Errors O0.67 75High Average
Verbal Fluency
Total Letter 551.67 95 Superior
Total Category 3.00 99Very Superior
Category Switching Total 1.67 95 Superior
Category Switching Accuracy 161.33 91Superior
Total Set-Loss Errors -1.67 Borderline
Total Repetition Errors -1.67 5 Borderline
Color-Word Interference
Color Naming 260.33 63Average
Word Reading 1.00 84High Average
Inhibition 381.00 84High Average
Inhibition/Switching 411.00 84High Average
Total Inhibition Errors 0.67 75 High Average
Total Inhibition/Switching Errors 0.67 12 7575High Average
Tower
Total Achievement Score 211.00 High Average
Conners' Continuous Performance Test (CPT
Clinical Profile, Confidence Index 51.93 

Non-Clinical
For the following subtests, only clinically elevated scores are reported
Omissions 1 30.41good performance
Hit RT 341.1 29.62a little fast
Response Style 0.01 23.83mildly atypical
Perseverations 0 32.79good performance
Hit SE Block Change 0.07 83.87MILDLY ATYPICAL
Hit RT ISI Change 0.03 32.72good performance
MEMORY
Wechsler Memory Scale - 4th ed. (WMS-IV)
Story Learning and Recall
Logical Memory 1 290.67 12 75High Average
Logical Memory II 290.67 12 High Average
Percent Retention 

100
51
Recognition (130) 26 75
Figure Learning and Recall
Visual Reproduction | 1.00 High Average
Visual Reproduction II 411.67 15 95 Superior
Percent Retention
Recognition (17) 

>75
California Verbal Learning Test - 2nd ed. (CVLT-II)
Page 7 of 9
Printed: 12/29/2014 12:37 PM 

Page 28 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07 / 2014 
Trial 1 8 0.50 55 108 68Average
Trial 2 
Trial 3 
Trial 4 

0. 50 
0. 50 
0. 50 
Trial 5 1.50 65123 93 Superior
Trials 1-5 Total 61 1.10 117 86 High Average
Learning Slope Trials 1-5 1.8 0.50 55 108 68Average
Trial B 6 -0.50 45 93 30 Average
Short Delay Free Recall 1.50 123 93Superior
Short Delay Cued Recall 14 1.00 115 84High Average
Long Delay Free Recall 14 1.00 115 84 High Average
Long Delay Cued Recall 15 1.00 115 84High Average
Semantic Clustering 1 0.50 55 108 68
Serial Clustering 0.2 -0.50 45 93 30
Total Repetitions* 15 2.00 130 08
Total Intrusions* 1 -0.50 45 93 30
Recognition Hits 16 0.50 55 108 Average
False Positives* 0 -0.50 45 93 30
Recognition Discriminability 4 1.00 60 115 84High Average
* error score with lower score indicating higher performance
Rey-Osterrieth Complex Figure Test
Immediate Recall 22.5-0.40 46 94 34 Average
Delayed Recall 22.50.1151102 55 Average
Percent Retention 

100
LANGUAGE
Wechsler Adult Intelligence Scale - 4th ed. (WAIS-IV)
Verbal Comprehension
Similarities 311.33 14 91Superior
Boston Naming Test 570.39 54106 63 Average
# Correct with Phonemic Cue
Narrative Writing 

See Body of Report
VISUOSPATIAL AND QUANTITATIVE
Wechsler Adult Intelligence Scale - 4th ed. (WAIS-IV)
Perceptual Reasoning
Matrix Reasoning 241.67 15 95Superior
Rey-Osterrieth Complex Figure Test
Copy 64122 93Superior
SYMPTOM VALIDITY
California Verbal Learning Test - 2nd ed. (CVLT-II)
Forced Choice Recognition 

16/16
MOTOR
Grooved Pegboard
Dominant 550.89 59113 81High Average
Non-Dominant 590.81 58112 79High Average
EMOTIONAL, BEHAVIORAL, AND ADAPTIVE
Beck Depression Inventory (BDI-II) 
PSWQ 

Minimal
Below Cutoff
Z-scores have a mean of O and a standard deviation of 1.
Standard Scores (SS) have a mean of 100 and a standard deviation of 15.
Page 8 of 9
Printed: 12/29/2014 12:37 PM 

Page 29 of 70

Partners HealthCare System, Inc. MRN: (BWH)
Partners
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 10/30/2014 13:35
Author: Electronically Signed by Clare T. Humphreys, Ph.D. 

Visit Date: 10/07/2014
Scaled Scores have a mean of 10 and a standard deviation of 3.
T-scores have a mean of 50 and a standard deviation of 10
Page 9 of 9
Printed: 12/29/2014 12:37 PM 

Page 30 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
08/29/2014 Patient Note Final Triggs, Daniel Venance,N.P.
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 08/29/2014 12:46
Author: Electronically Signed by Daniel Venance Triggs,N.P. 

Visit Date: 08/29/2014
August 29,2014
Steven Keating
MRN#
Mr Keating, with his parents and girlfriend, were seen in clinic today for suture removal. His suture line was clean, dry and intact without signs of
infection. We discussed post suture care, including keeping the site open to air and keeping it dry for another 24 hours. He was instructed to call
the clinic for tempuature greater than 101.5, any drainage or reddness.
We discussed that his pathology was still pending and that I would notify him with the pathology once it is available. We also
discussed that he wil be followed by Dr. Wen at DFCI for which he already has an appointment in early September.
He has a good understanding of the above instructions.
Daniel Triggs, ANP-BC
Nurse Practitioner
Dept. of Neurosurgery
Page 1 of 1
Printed: 12/29/2014 12:37 PM 

Page 31 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
08/14/2014 Patient Note Final Sobieszczyk, Piotr S., M.D.
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 08/18/2014 15:51
Author: Electronically Signed by Piotr S. Sobieszczyk, M.D. 

Visit Date: 08/14/2014
I have evaluated Mr. Keating briefly in the recovery room after cerebral angiography. I was examining a different patient and was asked
for assistance by the nursing staff. Mr. Keating had an earlier vasovagal episode and had another episode with nausea, diaphoresis and
feeling faint. By the time I walked over, he was alert, oriented with normal heart rate, normal pressure, bounding pulses. He reported
that this episode felt like the earlier vasovagal event immediately after the angiogram. There was no evidence of arrhythmia. He was
stable and no further cardiac evaluation was deemed necessary.
Page 1 of 1
Printed: 12/29/2014 12:37 PM 

Page 32 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
08/07/2014 Note Final Chiocca, Ennio A., M.D., Ph.D.
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 08/16/2014 10:17
Author: Electronically signed by Ennio A. Chiocca, M.D., Ph.D. 
Patient: KEATING,STEVEN [ 

Visit Date: 08/07/2014
] M
Date of Visit: 08/07/2014
08/07/2014
RE: 

KEATING, STEVEN
MRN:
Leigh Firn, MD
MIT Medical
77 Massachusetts Avenue, E23
Cambridge, MA 02139
Dear Dr. Firn,
I am seeing today in followup, Mr. Keating. He decided to undergo surgery. We had a functional MRI showing that his speech
area has been pushed by the tumor from its usual location. We discussed with him the risks and complications of the surgery.
We will plan to do this with him awake to monitor speech, and also within the Amigo intraoperative MRI suite. I will obtain a
CT angiogram to confirm the lenticulo striate vessels are pushed away from the tumor.
All his questions were answered, as well as questions related to the disposition of his tissues for research and other genetic testing.
Sincerely,
Ennio Chiocca, MD, PhD
Ennio A. Chiocca, M.D., Ph.D.
Page 1 of 1
Printed: 12/29/2014 12:37 PM 

Page 33 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
08/01/2014 Note Final Chiocca, Ennio A., M.D., Ph.D.
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 08/05/2014 13:08
Author: Electronically signed by Ennio A. Chiocca, M.D., Ph.D. 

Visit Date: 08/ 01 / 2014 
Patient: KEATING,STEVEN J [ 29604774(BWH)] M
Date of Visit: 08/01/2014
08/01/2014
RE: 

KEATING, STEVEN
MRN:
Leigh Firn, MD
MIT Medical
77 Massachusetts Avenue, E23
Cambridge, MA 02139
Dear Dr. Firn,
This is a 26-year-old right-handed white male who used to live in Canada. In 2007, he participated in a functional MRI research
study. At that time, he was called back saying that this was a lesion in his left frontal area. He was told that this lesion could be
followed because it was small. Over the years, he has had serial MRI scans, the last one in Canada in October 2010 did not
show growth of the lesion. He was then lost to follow up. However, in the last week, he developed the equivalent of a seizure
like activity. This has involved lightheadedness, deja vu type feelings, smells, and left eye twitching. He had no loss of
consciousness. These episodes were followed by dull headaches. He was started on Keppra and then on MRI scan was
performed. This showed a large left frontal and insular lesion. He comes in today for followup. They obtained my name from a
neurosurgeon that knows his PhD advisor. He otherwise has had no speech issues. He had no memory issues.
MEDICATIONS: He is currently taking Keppra 50 mg p.o. twice a day.
FAMILY HISTORY: There is no family history of brain disease of brain cancer.
SOCIAL HISTORY: He does not use of tobacco. He is currently a PhD student and works on 3D printing. He occasionally
drinks. He is here not only with his PhD advisor, but also with his parents and other relatives.
PHYSICAL EXAMINATION: On examination, he is completely awake and alert. There are no focal neurological symptoms
or signs that I can tell.
IMAGING: His MRI scan shows a large left frontal and insular lesion that involves the operculum in the front where it seems to
be involving Broca's area. There is a little bit of the tumor in the left anterior temporal lobe as well. The tumor is T2 and FLAIR
hyperintense. It does put pressure with some left and right shift of the brain, particularly anteriorly.
ASSESSSMENT AND PLAN: I had a long discussion with the patient. This is likely a low-grade glioma. We discussed
potential approaches. I think we should proceed with a functional MRI as well as a 2HG MRI scan. The functional MRI would
be for presurgical planning to distinguish where Broca's area is. Based on this, it would be helpful to also figure out if the
functional MRI showed that his speech is totally on the left side, which is what I expect. We will also get a CT angiogram to see
where the lenticulostriate vessels are. The plan will be for him to proceed with an attempted gross total resection of the lesion.
This could be done with the patient awake and also potentially in the intraoperative MRI suite.
I did discuss some of the risks and complications from the surgery as well. I did tell him that after the functional MRI scan and a
CT angiogram, we should meet again at least 1 more time to go over the potential risks. They want to think about their options.
They also have a consultation pending or they have already obtained this yesterday from Massachusetts General Hospital. I have
told him that either place will be well suited for this operation.
Page 1 of 2
Printed: 12/29/2014 12:37 PM 

Page 34 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Notes from 1/1/2004 through 12/29/2014 (cont)
Patient: KEATING,STEVEN WH) 04/29/88 U Signed 08/05/2014 13:08
Author: Electronically Signed by Ennio A. Chiocca, M.D., Ph.D. 

Visit Date: 08/01/2014
I did spend over half of the 60-minute visit counseling the patient.
Sincerely,
Ennio Chiocca, MD, PhD
Ennio A. Chiocca, M.D., Ph.D.
Page 2 of 2
Printed: 12/29/2014 12:37 PM 

Page 35 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Operative Report From 1/1/2004 through 12/29/2014
08/19/2014 1. Awake left frontotempo Signed
Date of Operation: 08/19/14 Report Status: Signed
SURGEON: CHIOCCA, ENNIO MD
ASSISTANT:
Peleg Horowitz, MD
PREOPERATIVE DIAGNOSIS:
Left frontal insular glioma.
POSTOPERATIVE DIAGNOSIS:
Left frontal insular glioma.
OPERATION:
1. Awake left frontotemporal craniotomy for resection of
low-grade glioma (Extensive approach and dissection).
2. Use of intraoperative MRI.
3. Computer assisted stereotactic navigation with the BrainLAB
device.
4. Use of microscope.
ESTIMATED BLOOD LOSS:
Less than 100 mL.
SPECIMEN REMOVED:
Left frontal and insular low-grade glioma.
INDICATIONS FOR PROCEDURE:
This is a 27-year-old student who is a student at MIT. Several

years ago, he a low-grade glioma diagnosed by MRI scan, which has
been followed. The last scan was in 2010. A few weeks ago, he had
a seizure and an MRI scan was performed revealing that this tumor
has enlarged considerably and this time it involves most of his
left frontal lobe, most of his left insula and is generating left to
right subfalcine herniation. A functional MRI was performed

showing that his speech/Broca's area was displaced superiorly,
but there is also speech in the superior temporal gyrus right
S
inferior to the insula as expected. He is brought to surgery for
resection of tumor.
DESCRIPTION OF PROCEDURE:
After obtaining informed consent, the patient was brought down to
the operating room (AMIGO suite). After the provision of MAC anesthesia, we
proceeded to anesthetize areas in his scalp. We provided to perform both a
scalp block as well as anesthesia in 3 areas for the pins. This allowed us to

fixate his head in a Mayfield cranial pin apparatus. We then
proceeded to pin his head onto the Mayfield. His head was
slightly turned with the left side up. We then made sure that
all of his body parts were well padded and then we proceeded to
obtain BrainLAB Coordinates. After obtaining the BrainLAB
coordinates, we proceeded to prep and drape the left side of his
11s 
scalp in usual a 

5
sterile fashion. We then proceeded to anesthesize the 
area of incision, and then proceeded to make a left frontotemporal
incision. We turned the scalp flap over a roll of sponges
and a little cuff of temporalis muscles was also incised. We then
proceeded to place bur holes in the temporal area and in the frontal
area next to the keel. This allowed us to turn a frontotemporal
Printed: 12/29/2014 12:37 PM 

Page 36 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Operative Report from 1/1/2004 through 12/29/2014 (cont)
craniotomy. After removing the bone flap, we proceeded to bite
down from the temporal bone inferiorly as well as some of the
frontal bone next to the sphenoid wing. After removing a large
piece of sphenoid keel, we proceeded to tent the dura
circumferentially. We then proceeded to cut the dura in a
circumferential fashion. The brain appeared to be relatively

full and therefore, the patient was given mannitol and also
Lasix. Preoperatively, he was also given some Decadron. I could
see discoloration in the left frontal area in front of the pars
triangularis. We proceeded to use the electrocortical stimulator
to stimulate and to see whether there was any speech arrest and none
was obtained. I then proceeded to make a generous 5-cm
corticectomy in his left inferior frontal gyrus. Then tediously

PBH
over the course of several hours, we painstakingly proceeded to
dissect the tumor in a subpial fashion. Inferiorly, we proceeded

to dissect the tumor from the base of the frontal lobe until we
encountered the olfactory nerve and then proceeded to go further, and
then encountered the gyrus rectus and proceeded to remove tumor
from the gyrus rectus, until the midline structures were
encountered. Inferiorly, I proceeded to dissect tumor off of the

sylvian fissure until we proceeded to encounter the insula. I entered
the insula in between the perysilvian vessel and proceeded to dissect tumor
from this area as well. The patient was speaking well throughout

this, but on several instances, especially as I was dissecting
superiorly and close to where the corona radiata was, there were
instances in which he had more trouble with speech in terms of
speech intelligibility. I would then stop and wait for a while

and his speech would return to almost normal. However, after
several hours of doing this, he was clearly getting very tired.
By this time, I dissected the tumor and a couple very large
pieces were sent off for pathology as well as additional genetic
studies and we had the tumor dissected completely off the
anterior cranial fossa in a subpial fashion. I

was also removing tumor anteriorly and got into the anterior temporal
lobe and proceeded to remove tumor off the anterior temporal lobe. I was able to
identify DE 

in a subpial fashion , the carotid artery , and then 
proceeded to dissect the tumor all the way from the top of the ICA to the middle
cerebral artery from proximal to distal. We finally encountered the
lenticulostriate vessels denoting the medial-inferior part of the tumot. All
this part was done using the
microscope. Additional dissection more superiorly, led us to encounter the
ventricle. There

was a small opening in the ventricle, but most of the ventricle
wall was left intact. I removed some tumor from the body of the

ventricle lateral as well as superior and a little bit inferior.
At this point, the patient was still speaking relatively well.
We proceeded therefore to obtain intraoperative MRI. The

intraoperative MRI appeared to show that we had a greater than
90% resection. There was some T2 abnormalities to the left in

the corona radiata as well as posteriorly along the sylvian
fissure and along the insula rim.
So we went back into the cavity and when I looked at
this, it clearly was a clot rather than tumor in all these areas
that I thought were tumor. After removing the clot with the
BrainLAB, it seemed that these T2 bright areas were mor consistent with
edematous brain or potentially infiltrated brain that potentially
could have been eloquent. I therefore desisted from further

surgery in this area. We then proceeded to line the cavity with
Printed: 12/29/2014 12:37 PM 

Page 37 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Operative Report from 1/1/2004 through 12/29/2014 (cont)
large sheets of Surgicel. We made sure the Surgicel was over the
0 
edges of the cortex in all directions. After, made sure that
there was good hemostasis, I proceeded to close. The dura was
closed primarily using interrupted HA 

sutures. After closing the
dura primarily, the bone flap was put back in position using
titanium plates and the middle of the bone flap was tented to the
1
dura. After doing this, we proceeded to irrigate again and
proceeded to close temporalis muscle, muscle fascia
galea and skin as per routine.
ATTESTATION:
I was present and scrubbed for the entire operation.
eScription documen 

HSSten Tel
Dictated By: CHIOCCA, ENNIO
Surgeon: CHIOCCA, ENNIO

H
Dictation ID
D: 08/19/14
T: 08/19/14
Electronically signed by ENNIO A. CHIOCCA, M.D., PH.D. on 08/25/14
Printed: 12/29/2014 12:37 PM 

Page 38 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology From 1/1/2004 through 12/29/2014
08/22/2014 Interpretive Lab Test Final
Accession Number: BL14K30690
Report Status: Final
Type: Interpretive Lab Test

Specimen Type: Paraffin embedded brain biopsy / BS14-N41488-B2
Procedure Date: 08/22/2014
Ordering Provider: ENNIO A. CHIOCCA M.D.
CASE: BL-14-K30690
PATIENT: STEVEN KEATING
Pathologist: 

Lynette M Sholl, M.D.
CLINICAL DATA:
Clinical History: None given.
Clinical Diagnosis: Astrocytoma
DNA was isolated from a brain tumor biopsy, BS14-41488-B2. DNA methylation
patterns in the CpG island of the MGMT gene (Genbank accession number AL355531
nt46931-47011) was determined by chemical (bisulfite) modification of
unmethylated, but not methylated, cytosines to uracil and subsequent PCR using
primers specific for either methylated or the modified unmethylated DNA
(Esteller et al. Cancer Reshylatethylated . 1999;59:79393--797.) The PCR products were analyzed
797P.
in duplicate parallel runs by capillary gel electrophoresis. The sensitivity of
2lectro
the assay based on DNA dilutions Sstudies s 

is at least 1:1000.
RESULT:
The analyzed region of the MGMT promoter is partially METHYLATED (1 of 2
aliquots).
INTERPRETATION:
MGMT (06-methylguanine DNA methyltransferase) is a DNA repair gene. Methylation
of the promotor leads to gene silencing and loss of MGMT expression. A recent
study that tested the methylation status of the same region of the MGMT
promoter in glioblastomas found that MGMT promoter methylation was an
independent favorable prognostic factor and was associated with a survival
benefit in patients treated with temozolamide and radiotherapy. (Hegi M,
Diserans A, Gorlia T et al. MGMT Gene Silencing and Benefit from Temozolomide
in Glioblastoma. N Engl J Med 2005;352:997-1003.)
These tests were developed and their performance characteristics determined by
the Molecular Diagnostics Laboratory, Brigham Hd and Women's Hospital. They have
not been cleared or approved by the U.S. Food and Drug Administration. The FDA

has determined that such clearance or approval is not necessary.
Final Diagnosis by Lynette M Sholl M.D., Electronically signed on Wednesday
September 03, 2014 at 04:53:20PM
Printed: 12/29/2014 12:37 PM 

Page 39 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
08/19/2014 Surgical Pathology Amend/Addenda
Accession Number: BS14N41488 
Type: Surgical Pathology
Specimen Type: LEFT FRONTAL TUMOR

Report Status: Amend/Addenda
Procedure Date: 08/19/2014
Ordering Provider: ENNIO A. CHIOCCA M.D.
CASE: BS-14-N41488
PATIENT: STEVEN KEATING
********** Addended Report ***********
Resident: David Meredith, M.D., Ph.D.
Pathologist: Umberto De Girolami, M.D.

PATHOLOGIC DIAGNOSIS:
A-D. SPECIMEN DESIGNATED "LEFT FRONTAL TUMOR" (FSA, SMA) :
NEWLY DIAGNOSED TUMOR (Surgery #1)
DIFFUSE ASTROCYTOMA, W.H.O. Grade 2 (ICD-0 9400/3)
IDH1 (R132H) MUTATION POSITIVE (by IHC)
TP53 PROTEIN 
BRAF (V600E) 

POSITIVE (by IHC, suggestive of mutation)
NOT DETECTED (by IHC)
NOTE:
There is evidence that the tumor may lie at the higher end of the grade 2
0
spectrum with focal regions having slightly higher than average cellularity and
atypia. Mitotic activity was detected in block B1, but this region was very
small (only a few high power fields) and mitoses were not detected in other
4
regions of the tumor. The proliferation . of rate in the region with mitotic
04
activity and the vast majority of .the tumor was low (not exceeding 4%).
OU
Therefore while grading as WHO Grade 3 was considered it was not felt to be
warranted at this time given the overall findings in a well sampled tumor.
Classification of the tumor as MIXED GLIOMA, WHO GRADE 2 would also be
10 

X
appropriate )given that reliable criteria for distinction of diffuse astrocytoma
M 

4
je
and mixed glioma have not been established and the clinical significance off
distinguishing between these two entities is not clear.
The overall size of the resection is very large.
The tumor infiltrates adjacent brain parenchyma.
W.H.O. Histologic Grading Criteria
Cellularity: 

moderate
DD
Atypia: 

moderate
(
Mitoses: 

present (but small focal region only)
P 
Vascular Proliferation: not present
Necrosis: 

not present 
Immunohistochemistry performed at BWH demonstrates the following staining
profile in lesional cells (block B1):
OLIG2 
GFAP 

positive (50% of cells, c/w astrocytoma)
positive (weak, variable)
lo
IDH1 (R132H) 
TP53 
Printed: 12/29/2014 12:37 PM 

positive (D(possibly heterogeneous ~70% of cells ) 
positive (50% of cells)
Page 40 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
Synaptophysin 
Neus 
SMI31 
BRAF (V600E) 

negative, no abnormal neurons 
negative, no abnormal neurons 
negative, no abnormal neurons 
negative
The formally quantified MIB-1 proliferation index is 2% (computer aided, block
Bl; 4/231 cells counted).
Analysis for MGMT promoter methylation status will be performed (block B2) and
the results reported separately by the BWH Center for Advanced Molecular
Diagnostics.
Array comparative genomic hybridization (Oncocopy) will be performed (block C1)
and results reported separately by the Cytogenetics laboratory.
Somatic mutation profiling (Oncopanel) will be performed (patient consented to
Oncopanel study 11-104).
Tumor Tissue Adequacy: 
Primary Advanced Study Block: ci, 2.5 cm (t60 n00), scrolls Ok
Secondary Advanced Study Blocks: B1, 2.5 cm (t60 n00), scrolls Ok
Clinical trial block: 
Tissue Microarray Block: 

Large {>1.0 cm in multiple blocks}
C1
C1
MGMT block:
Tissue submitted to tissue bank: Yes
Clinical frozen tissue: 
Consent Status for Tissue Research: Full 11-104, 10-417

Yes
The case was reviewed at the Neuropathology Staff Conference.
PATHOLOGY CLINICAL NOTES: 26 year old male with non-enhancing left frontal mass
discovered in 2007 via research fMRI. Followed with serial scans until 2010.
Now presents with seizure-like symptoms and increased size of the mass compared
to last imaging in 2010.
CLINICAL DATA:
History: Not given.
Operation: Not given.
Operative Findings: Not given.
Clinical Diagnosis: Left frontal tumor.
TISSUE SUBMITTED:
A/1. Left frontal tumor.
B/2. Left frontal tumor.
C/3. Left frontal tumor.
D/4. Left frontal tumor.

O.R. CONSULTATION:
SPECIMEN LABELED "#1. LEFT FRONTAL TUMOR" (FSA, SMA) :
Glioma without definite anaplastic features; further classification and
final grading awaits permanent sections.
OR Consultation by: Umberto De Girolami, M.D.
Resident: David Meredith, M.D., Ph.D.
The senior physician certifies that he/she personally conducted a gross and/or
microscopic examination of the described specimen (s) and rendered or confirmed
the rapid diagnos (es) related thereto.
Printed: 12/29/2014 12:37 PM 

Page 41 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
GROSS DESCRIPTION:
The specimen is received fresh, in four parts, each labeled with the patient's
name and unit number.
A
Part A, labeled "#1 Left frontal tumor" consists of an irregular, tan-pink,
0
gelatinous soft tissue fragment (4.0 x 1.6 x 0.9 cm). A representative section
is frozen as FSA and smeared as SMA. Representative sections are submitted for
research and for Oncopanel.
Micro A1: FSA remnant, 1 frag, ESS.
Micro A2: Multi frags, ESS.
Part B, labeled "#2 Left frontal tumor" consists of an irregular, tan-white to
tan-gray soft tissue fragment (4.5 x 2.5 x 2.0 cm). A representative section
is given to the tissue bank, clinically frozen and given for research. The

remainder is entirely submitted.
Micro B1-B2: Multi frags toto, ESS.
Part C, labeled "#3 Left frontal tumor" consists of multiple tan-pink soft
tissue fragments (4.0 x 3.0 x 2.0 cm in aggregate). A representative section
is given for research and clinically frozen. The remainder is entirely

submitted.
Micro C1-C4: Multi frags toto, ESS.
Part D, labeled "#4 Left frontal tumor" consists of multiple irregular,
tan-white soft tissue fragments (2.8 x 1.7 x 1.2 cm in aggregate), which are
submitted in toto.
Micro D1-D2: Multi frags, ESS.
CASE NUMBER: 41488
Dictated by: Taft, Kristin
DK
By his/her signature below, the senior physician certifies that he/she
personally conducted a microscopic examination ("gross only" exam if so stated)
th 
of the described specimen (s) and rendered or confirmed the diagnosis (es)
related рон 
Final Diagnosis by Keith L Ligon M.D., Ph.D., Electronically signed on

thereto.
Saturday September 06, 2014 at 07:35:53PM
ADDENDUM:
Results of Oncocopy (array CGH) were reviewed and found to support the
histopathologic diagnosis of a low grade glioma without unfavorable features.
INTEGRATIVE DIAGNOSIS (including histopathology, IHC, and array CGH results):
DIFFUSE ASTROCYTOMA
GRADE 2
IDH1 (R132H) MUTATION POSITIVE
This concludes all planned clinical testing on the case.
Printed: 12/29/2014 12:37 PM 

Page 42 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
Addendum #1 by Keith L Ligon M.D., Ph.D., Electronically signed on Saturday
September 06, 2014 at 07:39:30 PM
Printed: 12/29/2014 12:37 PM 

Page 43 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
08/19/2014 Cytogenetics Final
Accession Number: CG14R05315 

Report Status: Final
Type: Cytogenetics
Specimen Type: cg-FFPE

Procedure Date: 08/19/2014
Ordering Provider: ENNIO A. CHIOCCA M.D.
CASE: CG-14-R05315
PATIENT: STEVEN KEATING
Cytogeneticist: Ligon Ph.D., Azra Hadi

SOLID TUMOR ARRAY CGH ANALYSIS
RESULT:
arr[hg19]
3q26.31928 (171,681,429-188,500,069)x3, 7p22.3226.2 (42,976-155,143,600) x3, (8)x3
INTERPRETATION:
Several copy number changes were identified following array comparative genomic
hybridization (aCGH) of this formalin-fixed, paraffin-embedded (FFPE) primary
brain tumor specimen. The following genomic imbalances were noted:

(1) a 16.8 Mb single copy gain of 3q, which includes PIK3CA and S0X2,
(2) polysomy 7
(3) polysomy 8
The findings are CONSISTENT the histopathologic diagnosis of a DIFFUSE
ASTROCYTOMĀ WHO GRADE 2 or other low grade IDH-mutated astrocytoma/mixed
glioma.
Gains involving Chr 7 and 8 are common in diffuse astrocytoma. In isolation
however, they are not specific or diagnostic of low grade glioma or any other
tumor type.
Aberrations commonly correlated with less favorable outcomes in diffuse
astrocytoma (PTEN/10q loss, CDKN2A/9q loss, etc) are NOT DETECTED.
The findings are NOT CONSISTENT with an oligodendroglioma as there is no
evidence for lp/199 co-deletion.
See Table 1 (below) for a list of selected genes/regions that were evaluated
specifically for this interpretation.
COMMENTS:
Array - based comparative genomic hybridization (aCGH) was performed using the
umn CGH 

7
stock 1x1M Agilent Sure Print G3 Human CGH Microarray chip to identify tumor -
specific genomic copy number changes. Genomic DNA isolated from the FFPE
specimen submitted was hybridized with genomic DNA isolated from a reference
DNA sample representing a pool of karyotypically normal individuals (Promega,
Madison, WI). The array platform contains 963,029 probes spaced across the
human genome with a 2.1 kb overall median probe spacing and a 1.8 kb probe
Printed: 12/29/2014 12:37 PM 

Page 44 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
spacing in RefSeq genes. A genomic imbalance is reported when a minimum of

eight (8) consecutive probes, which correspond to approximately 14-16 kb, show
an average log2 ratio above +0.18 or below -0.30. Amplifications are reported

when an average log2 ratio for a given interval is equal to, or greater than,
+2.0.
This assay cannot exclude: (1) chromosome imbalances when the proportion of
tumor cells in the original sample is less than 50%; (2) chromosome imbalances
smaller than the resolution of the chip, or (3) tumor heterogeneity,
particularly if an abnormal clone is not sufficiently represented in the
original sample. This assay is not designed to identify balanced chromosomal

R
rearrangements (e.g., balanced reciprocal translocations, inversions or
OR 
insertions), ploidy changes, uniparental disomy or DNA methylation. The

composition of this array is based on the UCSC hg19 (GRCh37), Feb. 2009
(http://genome.ucsc.edu/cgi-bin/hgGateway). This test was developed and its

performance determined by the BWH Cytogenetics Laboratory as required by the
CLIA '88 regulations. This test is used for clinical purposes.

INDICATION FOR TEST:
Astrocytoma
BS14-N41488-C1
TABLE 1:
Gene/Region Chromosome Band Copy Number Change Nucleotides
(GRCh377/hg19)
MYCL1 1p34.2 No change detected
CDKN2C 1p33 No change detected
PIK3C2B 1932agommm..1 No change detected
MDM4 1932.1 No change detected

AKT3 1944 No change detected
MYCN 2p24.3 No change detected

PIK3CA 3926.32 16.8 Mb single copy gain chr3:171,681,429-188,500,069
ON
hz
SOX2 3926.33 16.8 Mb single copy gain chr3:171,681,429-188,500,069

FGFR3 4p16.3 No change detected
PDGFRA 4912 No change detected
MYB 6923.3 No change detected
PARK2 6926 No change detected

EGFR 7p11.2 Single Copy gain/polvsomv chr7:42,976-155,143,600
EGFRVIII 7p11.2 Not detected

CDK6 7921.2 Single copy gain/polysomy chr7:42,976-155,143,600
NN
MET 7931.2 Single copy gain/polysomy chr7:42,976-155,143,600
BRAF 7934 Single copy gain/polysomy chr7:42,976-155, 143,600

FGFR1 8p11.23-p11.22 Single copy gain/polysomy chr8:161,472-145,978, 744
MYC 8224.21 Single copy gain/polysomy chr8:161,472-145,978, 744
CDKN2A 9p21.3 No change detected
PTEN 10923.31 No change detected
FGFR2 10926.13 No change detected

121
CCND2 12p13.32 No change detected
Ο 
CDK4 12q14.1 No change detected

Ο 
MDM2 12915 No change detected

Ο
RB1 13914.2 No change detected

Ο 
TP53 17p13.1 No change detected
Ο c
NF1 17q11.2 No change detected

NNMONΟ
INI1 22q11.23 No change detected
Printed: 12/29/2014 12:37 PM 

Page 45 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Pathology from 1/1/2004 through 12/29/2014 (cont)
NF2 22q12.2 No change detected

1p- N/A Whole arm loss not detected
4p- N/A Whole arm loss not detected
Monosomy 6 N/A Not detected
69- N/A Whole arm loss not detected

Polysomy 7 N/A Detected chr7:42,976-155,143,600
7p- N/A Whole arm loss not detected
Monosomy 10 N/A Not detected

109- N/A Whole arm loss not detected
11p- N/A Whole arm loss not detected
Monosomy 14 N/A Not detected
idic (17p11.2) N/A Not detected

187- N/A Whole arm loss not detected
199- N/A Whole arm loss not detected
Monosomy 22 N/A Not detected

Other:
Polysomy 8 N/A Detected
REPORT by Azra Hadi Ligon Ph.D., on Wednesday September 03, 2014 at

11:30:18 AM
Final Diagnosis by Keith L Ligon M.D., Ph.D., Electronically signed on
Saturday September 06, 2014 at 06:30:36 PM
Printed: 12/29/2014 12:37 PM 

Page 46 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Radiology From 1/1/2004 through 12/29/2014
11/05/2014 17:11 MR Brain w/w/o Contrast AND FurSeq Final
Exam Number: A14026450 

Report Status: Final
Type: MR Brain w/w/o Contrast AND Furseq
Date/Time: 11/05/2014 17:11

Exam Code: MS0553
Ordering Provider: WEN MD, PATRICK YUNG
REPORT:
MRI BRAIN PRE AND POST IV CONTRAST
INDICATION: SSX:Perfusion imaging +/- Gad, flair, HX:Glioma. Per
electronic medical ed 

record, patient is a 26 - year - old male with
history of left frontal astrocytoma grade 2 status post resection
in August 19, 2014 currently in consideration for radiation
therapy.
COMPARISON: December 5, 2007, August 8, 2014, August 20, 2014,
and October 1, 2014
TECHNIQUE: Multiplanar, multisequence imaging of the brain was
performed both pre- and post contrast administration.
24 mL of gadolinium contrast (Magnevist) was administered IV,
uneventfully.
The following specific sequences were acquired: 3 plane
localizer, sagittal T1, axial FLAIR, coronal FLAIR, sagittal T1
preand postcontrast, susceptibility weighted, axial T2, axial
diffusion-weighted with ADC map, 3-D axial T1 MP rage with
coronal and sagittal reformats, and perfusion sequences.
FINDINGS:
Postsurgical change related to prior left frontal craniotomy and
resection of the nonenhancing mass is again seen with areas of
susceptibility, consistent with hemorrhagic products from
surgery. The small subdural collection layering along the left.
frontal lobe is .again seen, which appears to have redistributed
P
without significant change in size compared to prior exam and
also demonstrates mild mass effect with partial effacement of
4
sulci and mild 4 mm left . 

to right midline shift . The resection 
cavity size has decreased in size compared to October 1, 2014.
Hd
P
Minimal areas of dural enhancement and rim enhancement within the
O
resection cavity .is again seen, similar/slightly improved
P
compared to prior exam and is likely related to postsurgical
. 
P
change. There is no evidence of enhancing masses or intermediate
th 
restricted diffusion to suggest high cellularity.
In the superior medial region of the resection cavity, the area
of thickened, nodular nonenhancing T2 signal abnormality appears
slightly increased compared to October 1, 2014 with evidence of
gradual increase in size and diffusivity in comparison to August
8, 2014. There is also subtle increase in nonenhancing abnormal
T2 prolongation within the right inferior medial frontal lobe in
the region of anterior commissure in comparison to October 1,
2014 and also to August 18, 2014 which is concerning for minimal
progression of infiltrative tumor.
There is no evidence of ependymal nodules or abnormal areas of
dural enhancement or leptomeningeal spread of disease.
Printed: 12/29/2014 12:37 PM 

Page 47 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Radiology from 1/1/2004 through 12/29/2014 (cont)
There BooPis no evidence of infarction. Similar linear CSF intensity
lesions are seen within the corpus callosum, unchanged from 2007
and most likely represents anatomic variant of dilated
perivascular space. The ventricles and sulci are mildly
prominent, however is unchanged compared to prior exam. Right
maxillary sinus mucus retention cyst. Otherwise rest of the
N
visualized paranasal sinuses and mastoid air cells are clear.
Orbits are unremarkable. There are normal flow-voids in the major
intracranial vessels. The skull base and calvarium demonstrate
normal signal.
Perfusion: There are no abnormal areas of increased blood volume.
IMPRESSION:
1. Gradual increase in volume of nodular low cellularity, low
vascularity tumor at the left superior medial aspect of resection
cavity since August 2014 with very slight increase in comparison
to October 1, concerning for gradual progression of nonenhancing
low grade tumor. Attention at follow up is suggested.
(D
2. Very gradual increase in nonenhancing abnormal along the
inferior medial right frontal lobe and anterior commissure
concerning for very gradual infiltrative progression. Attention
at follow up is suggested.HP 
3. Interval decrease in size of the resection cavity likely

.
related to evolution of postoperative findings and slight growth
of nodular lesion along the left superior medial aspect of
resection OS cavity.
4. Interval .redistribution of left frontal subdural collection
3 

P 
without definite change in size or mild mass effect and minimal
midline shift.
I, the teaching physician, have reviewed the images and agree
with the report as written.
1.
This report was electronically signed by GEOFFREY YOUNG MD (T)
RADIOLOGISTS: 

SIGNATURES:
KIM, (R), HANSOL MD
YOUNG, MD (T), GEOFFREY S 
Finalized on: 
Printed: 12/29/2014 12:37 PM 

YOUNG, MD (T), GEOFFREY S
11/06/2014 18:28
Page 48 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Radiology from 1/1/2004 through 12/29/2014 (cont)
10/01/2014 16:22 MRI BRAIN W W/O CONTRAST 70553 Final
Exam Number: A13960521 

Report Status: Final
Type: MRI BRAIN W W/O CONTRAST 70553
Date/Time: 10/01/2014 16:22
Exam Code: 77790

Ordering Provider: WEN MD, PATRICK YUNG
REPORT:
MRI BRAIN WITH AND WITHOUT IV CONTRAST
INDICATION: 26-year-old male with glioma.
COMPARISON: MRI from August 20, 2014
TECHNIQUE: Multiplanar, multisequence MRI of the brain was
t x Contr O
performed with and without IV contrast. The following sequences

DO
were obtained: 3 plane localizers, sagittal Ti, coronal FLAIR,

(
axial FLAIR, Tl weighed images were performed without contrast.
During 22.5 ml Magnevist intravenous gadolinium contrast
administration, dynamic perfusion axial EPI images with delayed
axial T2, DWI, T1 and 3-D SPGR images with coronal and sagittal
m (. -a
reformation were performed. Perfusion data was wapostprocessedces

off-line by the interpreting radiologists and CBV maps were
produced.
FINDINGS:
Postoperative changes from prior left frontal craniotomy
including a resection cavity in the left frontal lobe are noted
with near complete resolution of blood product within the cavity
and interval decrease in the size of cavity. The subdural
collection along left convexity has slightly increased. The
Φ
pneumocephalus has resolved. The regions of T2 prolongation

surrounding the resection cavity has not significant changed,
although the thickness of abnormality medially and posteriorly
slightly increased which could be secondary to contraction ofоно
resection cavity. There is no focal decreased diffusivity.
Following contrast administration, there is mild linear
enhancement along the cavity.
Perfusion imaging shows no evidence of increased blood volume in
the regions of signal abnormality or elsewhere in the brain.
IMPRESSION:
Postsurgical changes with a resection cavity in the left frontal
PHO
lobe, with interval slight increase in the size of subdural
collection along left convexity. The regions of T2 abnormality
medial and posterior to the cavity appear slightly more
prominent, which may be secondary to contraction of cavity versus
nonenhancing tumor growth. Mild linear enhancement along cavity
most likely postsurgical. No evidence of enhancing, hypervascular
or hypercellular tumor progression.
Critical results were communicated and documented using the Alert
Notification of Critical Radiology Results (ANCR) system.
Printed: 12/29/2014 12:37 PM 

Page 49 of 70

Partners HealthCare System, Inc. MRN: (BWH)
BRIGHAM & WOMEN'S HOSPITAL 

KEATING,STEVEN
A Teaching Affiliate of Harvard Medical School
Date of Birth: 04/29/1988
75 Francis Street, Boston, Massachusetts 02115
Age: 26 yrs. Sex: M
Radiology from 1/1/2004 through 12/29/2014 (cont)
This report was electronically signed by RAYMOND HUANG MD (T)
RADIOLOGISTS: 
HUANG, MD (T), RAYMOND 
Finalized on: 
Printed: 12/29/2014 12:37 PM 

SIGNATURES:
HUANG, MD (T), RAYMOND
10/01/2014 17:36
Page 50 of 70
"""
