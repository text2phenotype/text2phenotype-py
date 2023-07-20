from enum import Enum

from django.core.management.base import BaseCommand

from text2phenotype.text2phenotype_auth.okta.client import OktaClient
from text2phenotype.text2phenotype_auth.okta.constants import OktaConstants
from text2phenotype.text2phenotype_auth.okta.exceptions import OktaClientError
from text2phenotype.text2phenotype_auth.okta.schemas import OktaUserIdentifier
from text2phenotype.common.log import operations_logger as log
from text2phenotype.constants.environment import Environment


class BaseOktaSetupCommand(BaseCommand):
    APPLICATION_TAG: str = 'MDL'
    CALLBACK_URL: str = '/'
    ENVIRONMENT_CLASS: Environment = Environment
    TEXT2PHENOTYPE_ADMIN_GROUP: str = 'name_of_text2phenotype_admin_group'
    PERMISSIONS_ENUM: Enum = Enum

    help = 'Do service-specific Okta setup: adds role groups groups & OIDC client + callback'

    def add_arguments(self, parser):
        parser.add_argument('--env_name', required=True, help='Customer or environment name')
        parser.add_argument('--env_url', required=True, help='Base URL (including protocol) for the environment. '
                                                             'Required to set up callback URL.')
        parser.add_argument('--idp', required=False, help='IdP ID from manually added Identity Provider '
                                                          'where all non-Text2phenotype users should authenticate.')

    def handle(self, *args, **options):
        client = OktaClient(tenant_url=self.ENVIRONMENT_CLASS.OKTA_TENANT_URL.value,
                            api_token=self.ENVIRONMENT_CLASS.OKTA_API_TOKEN.value,
                            app_name=OktaConstants.Apps.INTEGRATION_PORTAL)

        env_name = options['env_name']
        env_url = options['env_url']
        idp = options.get('idp')

        # Add role groups for all roles in StandardRoles
        role_groups = client.add_role_groups(app_name=self.APPLICATION_TAG, roles=self.PERMISSIONS_ENUM.get_values())
        text2phenotype_admin_group = role_groups[self.TEXT2PHENOTYPE_ADMIN_GROUP]

        # Get ID for Text2phenotype Users group...
        results = client.search_groups(OktaConstants.Groups.TEXT2PHENOTYPE_USERS)
        for grp in results:
            if grp.name == OktaConstants.Groups.TEXT2PHENOTYPE_USERS:
                text2phenotype_group_id = grp.id
                break
        else:
            log.error(f'Group named `{OktaConstants.Groups.TEXT2PHENOTYPE_USERS}` does not exist!')
            raise OktaClientError(msg=f'Group named `{OktaConstants.Groups.TEXT2PHENOTYPE_USERS}` does not exist!')

        log.info(f'`{OktaConstants.Groups.TEXT2PHENOTYPE_USERS}` group ID: {text2phenotype_group_id}')

        client.add_group_rule_text2phenotype_role(name=f'Give Text2phenotype users default admin role - {self.APPLICATION_TAG}',
                                         user_group=text2phenotype_group_id,
                                         role_group=text2phenotype_admin_group)

        # Create OpenID/OAuth2 Client Application for this environment
        app = client.add_application(dns=env_url.strip('/'), name=f'{env_name}-{self.APPLICATION_TAG}',
                                     callback=self.CALLBACK_URL)

        # Assign Customer Group to this Client, along with Text2phenotype Users group
        assign_groups = [text2phenotype_group_id, self.ENVIRONMENT_CLASS.OKTA_CUSTOMER_GROUP_ID.value]
        client.assign_groups_to_application(app_id=app.id, groups=assign_groups)
        log.info(f'Client app ID: {app.id}')

        if idp:
            # do IDP setup
            log.info('Adding customer group assignment for users who authenticate '
                     'through customer IdP and set customer IdP as profile master...')
            idp_data = client.get_idp(idp)

            provisioning_config = idp_data['policy']['provisioning']
            provisioning_config['profileMaster'] = True

            groups_config = provisioning_config['groups']
            groups_config['action'] = 'ASSIGN'
            groups_config['assignments'] = [self.ENVIRONMENT_CLASS.OKTA_CUSTOMER_GROUP_ID.value]

            client.update_idp(idp_data)

            # Adding routing rules for customer users...
            client.add_routing_rule(
                name=f'{env_name} -> IdP {idp}',
                priority=3,
                okta=False,
                idp_id=idp,
                app_include_id=app.id,
                user_identifier=OktaUserIdentifier(),
            )

        log.info(f'\nPreserve the following values for use in the environment '
                 f'(they can also be retrieved from the Okta console):\n'
                 f'{"*" * 76}\n** ' +
                 '{:<70}'.format(f'Okta Client ID: {app.client_id}') +
                 f' **\n** ' +
                 '{:<70}'.format(f'Okta Client Secret: {app.client_secret}') +
                 f' **\n'
                 f'{"*" * 76}\n')
