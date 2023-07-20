from enum import IntEnum
from text2phenotype.text2phenotype_auth.okta.constants import OktaAppNames


class Applications(IntEnum):
    INTEGRATION_PORTAL = 1
    SANDS = 2

class AuthConst:
    OKTA_CALLBACK = '/oauthcallback/okta/'


class SwaggerStrings:
    TEST_SUB = 'test@text2phenotype.com'
    TEST_PW = 'testpw'


# Other Constants
AppNameOkta2DB = {
    OktaAppNames.SANDS: Applications.SANDS.value,
    OktaAppNames.INTEGRATION_PORTAL: Applications.INTEGRATION_PORTAL.value,
}

AppNameDB2Okta = {}
for k, v in AppNameOkta2DB.items():
    AppNameDB2Okta[v] = k