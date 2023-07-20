import os
from typing import List, Tuple

from .colon157 import filepaths as colon157fps
from .colon158 import filepaths as colon158fps
from .david_vaughan import filepaths as davidvfps
from .john_stevens import filepaths as johnsfps
from .lung139 import filepaths as l139fps
from .lung143 import filepaths as l143fps
from .lung144 import filepaths as l144fps
from .lung146 import filepaths as l146fps
from .lung147 import filepaths as l147fps
from .Sample_MR_Buster_Bluthe import filepaths as busterbfps
from .Sample_MR_Dewe_Treatem import filepaths as dewetfps
from .Sample_MR_Jane_Doe import filepaths as janedfps
from .Sample_MR_John_Brown import filepaths as jbrownfps
from .Sample_MR_John_Tartar import filepaths as jtartarfps
from .Sample_MR_L_Diaz import filepaths as ldiazfps
from .Sample_MR_LH import filepaths as mrlhfps
from .Sample_MR_Mr_H import filepaths as mrhfps
from .Sample_MR_Mrs_JB import filepaths as mjbfps
from .Sample_MR_Mrs_LLY import filepaths as llyfps
from .Sample_MR_Mrs_X import filepaths as mrsxfps
from .Sample_MR_Richard_Smith import filepaths as richsfps
from .Sample_MR_Steve_Apple import filepaths as applefps
from .Sample_MR_Tan import filepaths as tanfps
from .Sample_MR_Tom_Gellato import filepaths as tgfps
from .sample_report1 import filepaths as sr1fps
from .sample_report2 import filepaths as sr2fps
from .SKM_C335118053015000 import filepaths as skm1fps
from .SKM_C335118053015010 import filepaths as skm2fps
from .SKM_C335118053015020 import filepaths as skm3fps
from .stephan_garcia import filepaths as sgfps
from .Steven_Keating_Health_Summary_Report import filepaths as skhsfps
from .Steven_Keating_HealthRecord_Dec29_2014 import filepaths as skhrfps
from .Steven_Keating_Pathology_Dec29_2014 import filepaths as skprfps
from .tina_mormol import filepaths as tmfps

biomed_636_fixtures_dir = os.path.dirname(__file__)

biomed_636_samples: List[Tuple] = [
    colon157fps,
    colon158fps,
    davidvfps,
    johnsfps,
    l139fps,
    l143fps,
    l144fps,
    l146fps,
    l147fps,
    busterbfps,
    dewetfps,
    janedfps,
    jbrownfps,
    jtartarfps,
    ldiazfps,
    mrlhfps,
    mrhfps,
    mjbfps,
    llyfps,
    mrsxfps,
    richsfps,
    applefps,
    tanfps,
    tgfps,
    sr1fps,
    sr2fps,
    skm1fps,
    skm2fps,
    skm3fps,
    sgfps,
    skhsfps,
    skhrfps,
    skprfps,
    tmfps
]
