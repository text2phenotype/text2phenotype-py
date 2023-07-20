from datetime import datetime
from typing import (
    Dict,
    Iterable,
    List,
    Tuple,
)

import requests
from django.utils.http import urlencode
from text2phenotype.common.log import operations_logger as log

from .constants import OktaConstants as Const
from .exceptions import OktaClientError
from .schemas import (
    OktaClientApp,
    OktaGoogleIDP,
    OktaGroup,
    OktaGroupClaim,
    OktaGroupRule,
    OktaRoutingRule,
    OktaUser,
    OktaUserAttribute,
    OktaUserIdentifier,
)


class OktaClient:
    def __init__(self, tenant_url: str, api_token: str, app_name: str = None,
                 env_name: str = None):
        self.tenant_url = tenant_url
        self.api_token = api_token
        self.app_name = app_name  # 'integration-portal', 'sands'
        self.env_name = env_name  # 'ECHO', 'Aruba', etc.

        self.header_data = {
            'Authorization': f'SSWS {self.api_token}',
            'Content-Type': Const.APPLICATION_JSON,
            'Accept': Const.APPLICATION_JSON,
        }

        self._authz_server = None
        self._idp_discovery_policy = None
        self._role_group_prefix = None

    @property
    def authz_server(self) -> str:
        if not self._authz_server:
            self._authz_server = self.get_default_authz_server()

        return self._authz_server

    @property
    def idp_discovery_policy(self) -> str:
        if not self._idp_discovery_policy:
            self._idp_discovery_policy = self.get_idp_discovery_policy()

        return self._idp_discovery_policy

    @property
    def role_group_prefix(self) -> str:
        if not self._role_group_prefix:
            self._role_group_prefix = f'{Const.Groups.ROLE_PREFIX}:'

        return self._role_group_prefix

    def add_application(self, dns: str, name: str, callback: str) -> OktaClientApp:
        log.info('Creating OpenID/OAuth2 client for this environment...')
        url = self._get_path(Const.Api.APPS)

        # Create the Client Application
        client_app = OktaClientApp(name=name, dns=dns, callback=callback)
        resp = self.post(url, data=client_app.to_dict())
        log.info('Creating OpenID/OAuth2 client for this environment...DONE')
        return OktaClientApp.from_dict(resp.json())

    def add_google_idp(self, client_id: str, client_secret: str,
                       text2phenotype_group_id: str) -> Tuple[str, str]:
        """
        Method adds the Text2phenotype Google OpenID connection and returns a tuple of
        the created IDP's:
        ID, Redirect URI
        """
        log.info('Adding Text2phenotype-ONLY Google OpenID IdP...')
        url = self._get_path(Const.Api.IDPS)

        google_idp = OktaGoogleIDP(client_secret=client_secret,
                                   client_id=client_id,
                                   text2phenotype_group_id=text2phenotype_group_id)
        resp = self.post(url, google_idp.to_dict())
        google_idp = resp.json()

        id = google_idp['id']
        redirect_uri = google_idp['_links']['clientRedirectUri']['href']

        log.info('Adding Text2phenotype-ONLY Google OpenID IdP...DONE')
        return id, redirect_uri

    def add_group(self, name: str, desc: str) -> OktaGroup:
        log.info(f'Adding {name} Group...')
        url = self._get_path(Const.Api.GROUPS)

        post_group = OktaGroup(name=name, description=desc)

        resp = self.post(url, post_group.to_dict())
        okta_group = OktaGroup.from_dict(resp.json())

        log.info(f'Added group {okta_group.name} (Group ID {okta_group.id}).')
        return okta_group

    def add_group_rule_text2phenotype_role(self, name: str, user_group: str, role_group: str):
        log.info('Adding group rule so Text2phenotype Users are assigned a default role...')
        url = self._get_path(Const.Api.GROUPS_RULES)

        group_rule = OktaGroupRule(name=name, user_group=user_group,
                                   role_group=role_group, priority=0)

        resp = self.post(url, data=group_rule.to_dict())

        # Activate rule
        rule = OktaGroupRule.from_dict(resp.json())
        url = self._get_detail_path(base=Const.Api.GROUPS_RULES,
                                    detail_id=rule.id,
                                    endpoint=Const.Api.GROUPS_RULES_ACTIVATE)
        self.post(url)
        log.info('Adding group rule so Text2phenotype Users are assigned a default role...DONE')

    def add_text2phenotype_provisioned_attribute(self):
        log.info('Adding custom attribute for Text2phenotype-provisioned users...')
        url = self._get_path(Const.Api.PROFILE)

        attr = OktaUserAttribute(attribute=Const.TEXT2PHENOTYPE_PROVISIONED_ATTR,
                                 title='Text2phenotype Provisioned',
                                 description='Did Text2phenotype provision this user?',
                                 data_type='boolean')
        self.post(url, attr.to_dict())
        log.info('Adding custom attribute for Text2phenotype-provisioned users...DONE')

    def add_role_groups(self, app_name: str, roles: Iterable) -> dict:
        log.info(f'Adding role groups for roles: {roles}...')

        result = dict()
        for role in roles:
            group_name = f'{self.role_group_prefix}{app_name}:{role}'
            resp = self.add_group(name=group_name, desc=group_name)
            result[role] = resp.id

        log.info(f'Adding role groups for roles: {roles}...DONE')
        return result

    def add_role_groups_claim(self):
        log.info('Adding custom claim for role groups...')
        url = self._get_detail_path(Const.Api.AUTHZ_SERVERS, self.authz_server,
                                    Const.Api.AUTHZ_SERVERS_CLAIMS)

        claim = OktaGroupClaim(name=Const.ROLE_GROUPS_CLAIM,
                               value=self.role_group_prefix)
        self.post(url, claim.to_dict())
        log.info('DONE')

    def add_routing_rule(self, name: str, priority: int,
                         user_identifier: OktaUserIdentifier = None,
                         app_include_id: str = None,
                         app_exclude_id: str = None,
                         okta: bool = True, idp_id: str = None):
        log.info(f'Adding routing rule {name}...')

        url = self._get_detail_path(base=Const.Api.POLICIES,
                                    detail_id=self.idp_discovery_policy,
                                    endpoint=Const.Api.POLICY_RULES)

        rule = OktaRoutingRule(name=name, priority=priority,
                               user_identifier=user_identifier,
                               app_include_id=app_include_id,
                               app_exclude_id=app_exclude_id,
                               okta=okta, idp_id=idp_id)
        self.post(url, rule.to_dict())
        log.info(f'Adding routing rule {name}...DONE')

    def add_default_routing_rules(self, google_idp: str):
        log.info('Adding default routing rules for Text2phenotype Internal and '
                 'Text2phenotype-Provisioned users...')

        # Text2phenotype Internal Users
        text2phenotype_internal = OktaUserIdentifier(type=OktaUserIdentifier.TypeOptions.IDENTIFIER,
                                            match=OktaUserIdentifier.MatchOptions.SUFFIX,
                                            value='text2phenotype.com')
        self.add_routing_rule(
            name='Text2phenotype Internal Users',
            priority=1,
            user_identifier=text2phenotype_internal,
            okta=False,
            idp_id=google_idp
        )

        # Text2phenotype-Provisioned Users
        text2phenotype_prov = OktaUserIdentifier(type=OktaUserIdentifier.TypeOptions.ATTRIBUTE,
                                        attribute=Const.TEXT2PHENOTYPE_PROVISIONED_ATTR,
                                        match=OktaUserIdentifier.MatchOptions.EQUALS,
                                        value=True)
        self.add_routing_rule(
            name='Text2phenotype-Provisioned Users',
            priority=2,
            user_identifier=text2phenotype_prov,
        )
        log.info('Adding default routing rules...DONE')

    def add_user_to_group(self, user_id: str, group_id: str):
        log.info(f'Adding user {user_id} to group {group_id}...')

        url = self._get_detail_path(Const.Api.GROUPS, detail_id=group_id,
                                    endpoint=Const.Api.GROUPS_USERS)
        url = f'{url}/{user_id}'
        self.put(url)
        log.info(f'Adding user {user_id} to group {group_id}...DONE')

    def assign_groups_to_application(self, app_id: str, groups: Iterable):
        log.info(f'Assigning groups {groups} to application {app_id}...')
        url = self._get_detail_path(Const.Api.APPS, app_id, Const.Api.APPS_GROUPS)
        for group_id in groups:
            data = {'id': group_id}
            self.put(f'{url}/{group_id}', data=data)
        log.info(f'Assigning groups {groups} to application {app_id}...DONE')

    def check_status(self) -> bool:
        url = self._get_path(Const.Api.LOGS,
                             query={'since': datetime.utcnow().isoformat()})

        try:
            self.get(url)
        except OktaClientError:
            return False
        else:
            return True

    def clear_user_sessions(self, user_id):
        log.info(f'Clearing sessions for user {user_id} in Okta...')
        url = self._get_detail_path(Const.Api.USERS, user_id,
                                    Const.Api.USERS_SESSIONS)
        self.delete(url)
        log.info('Sessions cleared.')

    def reset_password(self, user_id):
        """ Resends invitation
        """
        log.info(f'Reset user password {user_id}...')
        url = self._get_detail_path(Const.Api.USERS, user_id, Const.Api.USERS_RESET_PASSWORD)
        self.post(url)

    def resend_invitation(self, user_id):
        """ Resets user's password
        Api can return link for resetting password, or it can be sent through the email.
        That depends on okta settings
        """
        log.info(f'Resend invitation to {user_id}...')
        url = self._get_detail_path(Const.Api.USERS, user_id, Const.Api.USERS_RESEND_INVITATION)
        self.post(url)

    def suspend_user(self, user_id):
        """ Suspends a user
        This operation can only be performed on users with an ACTIVE status.
        The user has a status of SUSPENDED when the process is complete.
        https://developer.okta.com/docs/reference/api/users/#suspend-user
        """
        log.info(f'Suspending user {user_id}...')
        url = self._get_detail_path(Const.Api.USERS, user_id, Const.Api.USERS_SUSPEND)
        self.post(url)
        log.info(f'User {user_id} suspended.')

    def unsuspend_user(self, user_id: str) -> None:
        """ Unsuspends a user and returns them to the ACTIVE state
        This operation can only be performed on users that have a SUSPENDED status.
        https://developer.okta.com/docs/reference/api/users/#unsuspend-user
        """
        log.info(f'Unsuspend user {user_id}...')
        url = self._get_detail_path(Const.Api.USERS, user_id, Const.Api.USERS_UNSUSPEND)
        self.post(url)
        log.info(f'User {user_id} unsuspended.')

    def deactivate_user(self, user_id):
        """ Deactivates a user
        The user's status is DEPROVISIONED when the deactivation process is complete.
        This action cannot be recovered!
        https://developer.okta.com/docs/reference/api/users/#deactivate-user
        """
        log.info(f'Deactivating user {user_id}...')
        url = self._get_detail_path(Const.Api.USERS, user_id, Const.Api.USERS_DEACTIVATE)
        self.post(url, {'sendEmail': True})
        log.info(f'User {user_id} deactivated.')

    def delete_user(self, user_id: str) -> None:
        """ Deletes a user permanently.
        This operation can only be performed on users that have a DEPROVISIONED status.
        This action cannot be recovered!
        https://developer.okta.com/docs/reference/api/users/#delete-user
        """
        log.info(f'Deleting user {user_id}...')
        url = f'{self._get_path(Const.Api.USERS)}/{user_id}'
        self.delete(url)
        log.info(f'User {user_id} deleted.')

    def get_default_authz_server(self) -> str:
        url = self._get_path(Const.Api.AUTHZ_SERVERS)

        resp = self.get(url)
        for authz_server in resp.json():
            if authz_server['name'] == 'default':
                log.info(f'Default authorization server id: {authz_server["id"]}')
                return authz_server['id']
        else:
            log.error('Default authorization server not found!')
            raise OktaClientError(msg='Default authorization server not found!')

    def get_idp(self, idp_id):
        log.info(f'Getting IDP info for {idp_id}...')
        url = self._get_detail_path(base=Const.Api.IDPS,
                                    detail_id=idp_id,
                                    endpoint='')
        resp = self.get(url)
        return resp.json()

    def get_idp_discovery_policy(self) -> str:
        url = self._get_path(Const.Api.POLICIES,
                             query={'type': 'IDP_DISCOVERY'})
        resp = self.get(url)
        policies = resp.json()
        if len(policies) != 1:
            log.error(f'Found different number of IDP_DISCOVERY Policies than expected! '
                      f'Found {len(policies)}, expected 1')
            raise OktaClientError(msg=f'Found different number of IDP_DISCOVERY Policies than expected! '
                                      f'Found {len(policies)}, expected 1')
        policy = policies[0]

        return policy['id']

    def get_all_users(self) -> List[Dict]:
        """ Returns a list of all users """
        response_data = []

        url = self._get_path(Const.Api.USERS)

        # The request must contain a status filter,
        # because without this the users who have a status DEPROVISIONED will be excluded
        # https://developer.okta.com/docs/reference/api/users/#list-all-users
        filter_str = ''
        for status in Const.UserStatus:
            if filter_str:
                filter_str += '+or+'
            filter_str += fr'status+eq+"{status}"'
        url = f'{url}?filter={filter_str}'

        resp = self.get(url)
        response_data.extend(resp.json())
        while resp.links.get('next'):
            resp = self.get(resp.links.get('next')['url'])
            response_data.extend(resp.json())

        return response_data

    def find_user(self, user_id: str) -> dict:
        """ Fetch a user by id, login, or login shortname if the short name is unambiguous. """
        url = self._get_path(Const.Api.USERS) + f'/{user_id}'
        resp = self.get(url)
        if resp.ok:
            return resp.json()
        log.debug('User not found')
        return {}

    def provision_user(self, first_name: str, last_name: str, email: str,
                       groups: list, password: str = None) -> str:
        log.info('Provisioning user...')

        url = self._get_path(Const.Api.USERS, query={'activate': True})
        user_in = OktaUser(first_name=first_name, last_name=last_name,
                           email=email, groups=groups, password=password)

        resp = self.post(url, data=user_in.to_dict())
        user_out = OktaUser.from_dict(resp.json())

        log.info('Provisioning user...DONE')
        return user_out.id

    def update_user_profile(self, user_id: str, **kwargs) -> None:
        log.info('Updating user profile parameters')
        url = f'{self._get_path(base=Const.Api.USERS)}/{user_id}'

        profile = OktaUser(email='', **kwargs).to_dict().get('profile')
        filtered_profile = {k: v for k, v in profile.items() if v}
        filtered_profile.pop('text2phenotypeProvisioned')

        post_data = {'profile': filtered_profile}
        self.post(url, data=post_data)

    def get_user_profile(self, user_id: str) -> OktaUser:
        log.info('Get users profile')
        url = f'{self._get_path(base=Const.Api.USERS)}/{user_id}'

        resp = self.get(url)
        return OktaUser.from_dict(resp.json())

    def remove_user_from_group(self, user_id: str, group_id: str):
        log.info(f'Removing user {user_id} from {group_id}...')

        url = self._get_detail_path(Const.Api.GROUPS, detail_id=group_id,
                                    endpoint=Const.Api.GROUPS_USERS)
        url = f'{url}/{user_id}'
        self.delete(url)
        log.info(f'Removing user {user_id} from {group_id}...DONE')

    def search_groups(self, query: str) -> list:
        log.info(f'Searching groups with query `{query}`...')

        url = self._get_path(Const.Api.GROUPS, query={'q': query})
        resp = self.get(url)

        groups = [OktaGroup.from_dict(grp) for grp in resp.json()]

        log.info(f'Searching groups with query `{query}`...DONE')
        return groups

    def search_groups_to_dir(self, query: str) -> dict:
        groups = self.search_groups(query)

        result = {}
        for group in groups:
            result[group.name] = group.id

        return result

    def update_idp(self, idp_data):
        log.info(f'Updating IdP {idp_data["id"]}...')
        url = self._get_detail_path(base=Const.Api.IDPS,
                                    detail_id=idp_data['id'],
                                    endpoint='')
        self.put(url, idp_data)
        log.info(f'Updating IdP {idp_data["id"]}...DONE')

    # UTILITY FUNCTIONS
    @staticmethod
    def __handle_response(response: requests.Response) -> requests.Response:
        if response.ok:
            return response

        log.error(f'Error making {response.request.method} request to {response.url}: {response.text}')
        raise OktaClientError(error_json=response.json())

    def delete(self, url) -> requests.Response:
        log.debug(f'Request to {url}, header_data={self.header_data}')
        resp = requests.delete(url, headers=self.header_data)
        return self.__handle_response(resp)

    def get(self, url) -> requests.Response:
        log.debug(f'Request to {url}, header_data={self.header_data}')
        resp = requests.get(url, headers=self.header_data)
        return self.__handle_response(resp)

    def post(self, url: str, data: dict = None) -> requests.Response:
        log.debug(f'Request to {url}, data={data}, header_data={self.header_data}')
        resp = requests.post(url, json=data, headers=self.header_data)
        return self.__handle_response(resp)

    def put(self, url: str, data: dict = None) -> requests.Response:
        log.debug(f'Request to {url}, data={data}, header_data={self.header_data}')
        resp = requests.put(url, json=data, headers=self.header_data)
        return self.__handle_response(resp)

    def _get_detail_path(self, base: str, detail_id: str, endpoint: str) -> str:
        return f'{self.tenant_url}{base}/{detail_id}{endpoint}'

    def _get_path(self, base: str, query: dict = None) -> str:
        url = f'{self.tenant_url}{base}'

        if query:
            url = f'{url}?{urlencode(query)}'

        return url
