"""
Defines constants used by Okta client and constants defining string-based
linkages consuming apps need to reference.
"""
import enum


class OktaApiConstants:
    BASE_PATH = '/api/v1'
    APPS = f'{BASE_PATH}/apps'
    APPS_GROUPS = '/groups'
    AUTHZ_SERVERS = f'{BASE_PATH}/authorizationServers'
    AUTHZ_SERVERS_CLAIMS = '/claims'
    CLIENTS = f'{BASE_PATH}/clients'
    GROUPS = f'{BASE_PATH}/groups'
    GROUPS_RULES = f'{GROUPS}/rules'
    GROUPS_RULES_ACTIVATE = '/lifecycle/activate'
    GROUPS_USERS = '/users'
    IDPS = f'{BASE_PATH}/idps'
    LOGS = f'{BASE_PATH}/logs'
    POLICIES = f'{BASE_PATH}/policies'
    POLICY_RULES = '/rules'
    PROFILE = f'{BASE_PATH}/meta/schemas/user/default'
    USERS = f'{BASE_PATH}/users'
    USERS_SUSPEND = '/lifecycle/suspend'
    USERS_UNSUSPEND = '/lifecycle/unsuspend'
    USERS_DEACTIVATE = '/lifecycle/deactivate'
    USERS_RESET_PASSWORD = '/lifecycle/reset_password?sendEmail=true'
    USERS_RESEND_INVITATION = '/lifecycle/reactivate?sendEmail=true'
    USERS_SESSIONS = '/sessions'


class OktaAppNames:
    INTEGRATION_PORTAL = 'integration-portal'
    SANDS = 'sands'


class OktaGroups:
    SANDS_USERS = 'Sands Users'
    TEXT2PHENOTYPE_USERS = 'Text2phenotype Users'
    CUST_PREFIX = 'customer'
    ROLE_PREFIX = 'role'


class UserStatus(str, enum.Enum):
    """ Reference https://developer.okta.com/docs/reference/api/users/#user-status """

    STAGED = 'STAGED'
    PROVISIONED = 'PROVISIONED'  # New user is added in Okta but not activated yet
    ACTIVE = 'ACTIVE'  # Active status
    RECOVERY = 'RECOVERY'  # Existing user, activated previously, is in password reset mode
    LOCKED_OUT = 'LOCKED_OUT'
    PASSWORD_EXPIRED = 'PASSWORD_EXPIRED'  # User password is expired
    SUSPENDED = 'SUSPENDED'
    DEPROVISIONED = 'DEPROVISIONED'  # Deactivated in Okta


class OktaConstants:
    APPLICATION_JSON = 'application/json'
    TEXT2PHENOTYPE_PROVISIONED_ATTR = 'text2phenotypeProvisioned'

    ROLE_GROUPS_CLAIM = 'role-groups'
    TEXT2PHENOTYPE_GROUPS_CLAIM = 'text2phenotype-groups'  # This claim appeared after migration to Cyan Okta tenant

    # Name-spaced Constants
    Apps = OktaAppNames
    Api = OktaApiConstants
    Groups = OktaGroups
    UserStatus = UserStatus
