import argparse

from text2phenotype.common.log import operations_logger as log
from text2phenotype.text2phenotype_auth.okta.client import OktaClient
from text2phenotype.text2phenotype_auth.okta.constants import OktaConstants as Const


parser = argparse.ArgumentParser(description='Set up new Okta tenant from scratch for Integration Portal. Script '
                                             'will add role groups, role-groups claim, default routing rules, '
                                             'custom attributes, etc.')
parser.add_argument('--tenant_url', required=True, help='URL of the Okta tenant')
parser.add_argument('--api_token', required=True, help='API token you generated for the Okta tenant')
parser.add_argument('--google_client_id', required=True, help='Google OAuth2 Client ID')
parser.add_argument('--google_client_secret', required=True, help='Google OAuth2 Client Secret')


def main(args):
    client = OktaClient(tenant_url=args.tenant_url,
                        api_token=args.api_token,
                        app_name=Const.Apps.INTEGRATION_PORTAL)

    # Create Default Groups (Text2phenotype Users + Role Groups)
    result = client.add_group(name=Const.Groups.TEXT2PHENOTYPE_USERS,
                              desc=Const.Groups.TEXT2PHENOTYPE_USERS)
    text2phenotype_users_group = result.id

    # Add Google IdP
    google_id, google_redirect = client.add_google_idp(client_id=args.google_client_id,
                                                       client_secret=args.google_client_secret,
                                                       text2phenotype_group_id=text2phenotype_users_group)

    # Add custom claim to get role groups for user as part of ID token
    client.add_role_groups_claim()

    # Add custom attribute for Text2phenotype-provisioned users
    client.add_text2phenotype_provisioned_attribute()

    # Add default routing rules for Text2phenotype Internal and Text2phenotype-Provisioned users
    client.add_default_routing_rules(google_idp=google_id)

    log.info('*' * 120)
    log.info(f"Wait!!! You're not finished yet.")
    log.info(f'From the Google Cloud Platform Console (project = `oauth-access-okta-text2phenotype-only`), you need to add the\n'
             f'following redirect uri to the Google OAuth 2.0 Client (name = `Okta [Text2phenotype Only]`) as an \n'
             f'`Authorized Redirect URI`: {google_redirect}')
    log.info('*' * 120)


if __name__ == '__main__':
    main(parser.parse_args())
