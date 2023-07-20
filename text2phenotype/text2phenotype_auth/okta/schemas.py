import enum

from typing import Any, List

from .constants import OktaConstants as Const


class OktaSchema:

    def to_dict(self) -> dict:
        pass

    @classmethod
    def from_dict(cls, data: dict):
        pass

    class Meta:
        abstract = True


class OktaGroup(OktaSchema):
    """
    Defines schema and Text2phenotype-important information regarding Okta Groups.
    """
    DESCRIPTION = 'description'
    ID = 'id'
    NAME = 'name'
    PROFILE = 'profile'

    def __init__(self, name: str, description: str, id: str = None):
        self.id = id  # not used in POST requests, for obvious reasons
        self.name = name
        self.description = description

    def to_dict(self) -> dict:
        data = {
            self.PROFILE: {
                self.NAME: self.name,
                self.DESCRIPTION: self.description,
            }
        }

        return data

    @classmethod
    def from_dict(cls, data):
        result = cls(name=data[cls.PROFILE][cls.NAME],
                     description=data[cls.PROFILE][cls.DESCRIPTION],
                     id=data[cls.ID])

        return result


class OktaGroupRule(OktaSchema):
    ID = 'id'
    NAME = 'name'
    PRIORITY = 'priorityOrder'

    def __init__(self, name: str, priority: int = None, user_group: str = None,
                 role_group: str = None, id: str = None):
        self.name = name
        self.user_group = user_group
        self.role_group = role_group
        self.priority = priority
        self.id = id

    def to_dict(self) -> dict:
        if self.priority is None:
            raise ValueError('`priority` value is required for requests!')

        rule_data = {
            "type": "group_rule",
            "status": "INACTIVE",  # Always created INACTIVE, regardless of value
            self.PRIORITY: self.priority,
            self.NAME: self.name,
            "conditions": {
                "expression": {
                    "type": "urn:okta:expression:1.0",
                    "value": f"""isMemberOfAnyGroup("{self.user_group}")"""
                }
            },
            "actions": {
                "assignUserToGroups": {
                    "groupIds": [
                        self.role_group
                    ]
                }
            }
        }

        return rule_data

    @classmethod
    def from_dict(cls, data):
        result = cls(name=data[cls.NAME], id=data[cls.ID])
        return result


class OktaGroupClaim(OktaSchema):

    def __init__(self, name: str, value: str, status: str = 'ACTIVE',
                 claim_type: str = 'IDENTITY', filter_type: str = 'STARTS_WITH'):
        self.name = name
        self.value = value
        self.status = status
        self.claim_type = claim_type
        self.group_filter_type = filter_type

    def to_dict(self) -> dict:
        claim_post_data = {
            'name': self.name,
            'status': self.status,
            'claimType': self.claim_type,
            'valueType': 'GROUPS',
            'value': self.value,
            'group_filter_type': self.group_filter_type,
            'alwaysIncludeInToken': True,
            'conditions': {
                'scopes': [],
            }
        }

        return claim_post_data


class OktaUserAttribute(OktaSchema):

    def __init__(self, attribute: str, title: str, description: str,
                 data_type: str, required: bool = False):
        self.attribute = attribute
        self.title = title
        self.description = description
        self.data_type = data_type
        self.required = required

    def to_dict(self) -> dict:
        data = {
            'definitions': {
                'custom': {
                    'id': '#custom',
                    'type': 'object',
                    'properties': {
                        self.attribute: {
                            'title': self.title,
                            'description': self.description,
                            'type': self.data_type,
                            'required': self.required,
                            'permissions': [
                                {
                                    'principal': 'SELF',
                                    'action': 'READ_ONLY'
                                }
                            ]
                        }
                    },
                    'required': []
                }
            }
        }

        return data


class OktaUserIdentifier(OktaSchema):
    class TypeOptions(enum.Enum):
        ATTRIBUTE = 'ATTRIBUTE'
        IDENTIFIER = 'IDENTIFIER'

    class MatchOptions(enum.Enum):
        EQUALS = 'EQUALS'
        SUFFIX = 'SUFFIX'

    def __init__(self, type: TypeOptions = None,
                 match: MatchOptions = None, value: Any = None,
                 attribute: str = None):

        if type == self.TypeOptions.ATTRIBUTE and not attribute:
            raise ValueError('`attribute` is required when type is `ATTRIBUTE`')

        self.type = type.value if type else None
        self.match = match.value if match else None
        self.value = value
        self.attribute = attribute

    def to_dict(self) -> dict:
        if self.type:
            patterns = [{'matchType': self.match, 'value': self.value}]
        else:
            patterns = []

        data = {
            'type': self.type,
            'patterns': patterns,
        }

        if self.type == self.TypeOptions.ATTRIBUTE.value:
            data['attribute'] = self.attribute

        return data


class OktaRoutingRule(OktaSchema):
    ID = 'id'
    TYPE = 'type'

    def __init__(self, name: str, priority: int,
                 user_identifier: OktaUserIdentifier,
                 app_include_id: str = None,
                 app_exclude_id: str = None,
                 okta: bool = True, idp_id: str = None):
        # fidelity check
        if not okta and idp_id is None:
            raise ValueError('`idp_id` is required with idp_okta is False')

        # Set Defaults
        include = [{self.TYPE: 'APP', self.ID: app_include_id}] if app_include_id else []
        exclude = [{self.TYPE: 'APP', self.ID: app_exclude_id}] if app_exclude_id else []
        provider_info = [{self.TYPE: 'OKTA'}] if okta else [{self.ID: idp_id}]

        # Build final data format
        self._data = {
            self.TYPE: 'IDP_DISCOVERY',
            'name': name,
            'priority': priority,
            'actions': {
                'idp': {'providers': provider_info},
            },
            'conditions': {
                'app': {
                    'include': include,
                    'exclude': exclude,
                },
                'network': {
                    'connection': 'ANYWHERE',
                },
                'platform': {
                    'include': [
                        {
                            self.TYPE: 'ANY',
                            'os': {self.TYPE: 'ANY'},
                        },
                    ],
                    'exclude': [],
                },
                'userIdentifier': user_identifier.to_dict(),
            },
        }

    def to_dict(self) -> dict:
        return self._data


class OktaClientApp(OktaSchema):
    CLIENT_ID = 'client_id'
    CLIENT_SECRET = 'client_secret'
    CLIENT_URI = 'client_uri'
    CREDENTIALS = 'credentials'
    ID = 'id'
    LABEL = 'label'
    OAUTH = 'oauthClient'
    REDIRECT_URIS = 'redirect_uris'
    SETTINGS = 'settings'

    def __init__(self, name: str, dns: str, callback: str, id: str = None,
                 client_id: str = None, client_secret: str = None):
        self.name = name
        self.dns = dns
        self.callback = callback
        self.id = id
        self.client_id = client_id
        self.client_secret = client_secret

    def to_dict(self) -> dict:
        data = {
            'name': 'oidc_client',
            self.LABEL: self.name,
            'signOnMode': 'OPENID_CONNECT',
            self.CREDENTIALS: {
                self.OAUTH: {
                    'token_endpoint_auth_method': 'client_secret_post'
                }
            },
            self.SETTINGS: {
                self.OAUTH: {
                    self.CLIENT_URI: self.dns,
                    self.REDIRECT_URIS: [
                        f'{self.dns}{self.callback}'
                    ],
                    'response_types': [
                        'code'
                    ],
                    'grant_types': [
                        'authorization_code'
                    ],
                    'application_type': 'web'
                }
            }
        }

        return data

    @classmethod
    def from_dict(cls, data: dict):
        settings = data[cls.SETTINGS][cls.OAUTH]
        creds = data[cls.CREDENTIALS][cls.OAUTH]

        result = cls(name=data[cls.LABEL], dns=settings[cls.CLIENT_URI],
                     callback=settings[cls.REDIRECT_URIS][0],
                     id=data[cls.ID], client_id=creds[cls.CLIENT_ID],
                     client_secret=creds[cls.CLIENT_SECRET])

        return result


class OktaGoogleIDP(OktaSchema):

    def __init__(self, client_id: str, client_secret: str, text2phenotype_group_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.text2phenotype_group_id = text2phenotype_group_id

    def to_dict(self) -> dict:
        idp_data = {
            'type': 'GOOGLE',
            'status': 'ACTIVE',
            'features': [],
            'name': 'Google [Text2phenotype Only]',
            'protocol': {
                'algorithms': {
                    'request': {
                        'signature': {
                            'algorithm': 'SHA-256',
                            'scope': 'REQUEST'
                        }
                    },
                    'response': {
                        'signature': {
                            'algorithm': 'SHA-256',
                            'scope': 'ANY'
                        }
                    }
                },
                'endpoints': {
                    'acs': {
                        'binding': 'HTTP-POST',
                        'type': 'INSTANCE'
                    },
                    'authorization': {
                        'binding': 'HTTP-REDIRECT',
                        'url': 'https://accounts.google.com/o/oauth2/auth'
                    },
                    'token': {
                        'binding': 'HTTP-POST',
                        'url': 'https://www.googleapis.com/oauth2/v3/token'
                    },
                    'userInfo': None,
                    'jwks': {
                        'binding': 'HTTP-REDIRECT'
                    }
                },
                'scopes': [
                    'email',
                    'openid',
                    'profile'
                ],
                'settings': {
                    'nameFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified'
                },
                'type': 'SAML2',
                'credentials': {
                    'client': {
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    }
                }
            },
            'policy': {
                'accountLink': {
                    'action': 'AUTO',
                    'filter': None
                },
                'provisioning': {
                    'action': 'AUTO',
                    'conditions': {
                        'deprovisioned': {
                            'action': 'NONE'
                        },
                        'suspended': {
                            'action': 'NONE'
                        }
                    },
                    'groups': {
                        'action': 'ASSIGN',
                        'assignments': [self.text2phenotype_group_id]
                    }
                },
                'maxClockSkew': 120000,
                'subject': {
                    'userNameTemplate': {
                        'template': 'idpuser.email'
                    },
                    'matchType': 'USERNAME',
                    'matchAttribute': ''
                }
            },
        }

        return idp_data


class OktaUser(OktaSchema):
    EMAIL = 'email'
    FIRST_NAME = 'firstName'
    GROUP_IDS = 'groupIds'
    ID = 'id'
    LAST_NAME = 'lastName'
    LOGIN = 'login'
    PROFILE = 'profile'
    PASSWORD = 'password'

    def __init__(self, first_name: str, last_name: str, email: str,
                 groups: List[str] = None, id: str = None, password: str = None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.groups = groups
        self.id = id
        self.password = password

    def to_dict(self) -> dict:
        data = {
            self.PROFILE: {
                self.FIRST_NAME: self.first_name,
                self.LAST_NAME: self.last_name,
                self.EMAIL: self.email,
                self.LOGIN: self.email,
                Const.TEXT2PHENOTYPE_PROVISIONED_ATTR: True
            },
            self.GROUP_IDS: self.groups,
        }
        if self.password:
            data.update({"credentials": {"password": {"value": self.password}}})
        return data

    @classmethod
    def from_dict(cls, data: dict):
        profile = data[cls.PROFILE]
        password = data.get('credentials', {}).get('password', {}).get('value')
        user = cls(first_name=profile[cls.FIRST_NAME],
                   last_name=profile[cls.LAST_NAME],
                   email=profile[cls.EMAIL],
                   id=data[cls.ID],
                   password=password)

        return user
