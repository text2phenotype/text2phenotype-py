import argparse

from text2phenotype.common.log import operations_logger as log
from text2phenotype.text2phenotype_auth.okta.client import OktaClient
from text2phenotype.text2phenotype_auth.okta.constants import OktaConstants as Const


parser = argparse.ArgumentParser(description="This script will set up a new customer or environment to use Okta. If "
                                             "the environment has its own Identity Provider, you will need to add "
                                             "that manually through Okta for the time being. Include the associated "
                                             "'IdP ID' in this script (--idp) to correctly form the routing rule.")
parser.add_argument('--tenant_url', required=True, help='URL of the Okta tenant')
parser.add_argument('--api_token', required=True, help='API token you generated for the Okta tenant')
parser.add_argument('--env_name', required=True, help='Customer or environment name')


def main(args):
    client = OktaClient(tenant_url=args.tenant_url,
                        api_token=args.api_token,
                        env_name=args.env_name)

    log.info(f'Adding customer group for {args.env_name}...')
    group = client.add_group(name=f'{Const.Groups.CUST_PREFIX}:{args.env_name}',
                             desc=f'Group to hold customer users for {args.env_name}.')

    log.info(f'\nPreserve the following value for use in the environment '
             f'(it can also be retrieved from the Okta console):\n'
             f'{"*" * 76}\n** ' +
             '{:<70}'.format(f'Okta Customer Group ID: {group.id}') +
             f' **\n{"*" * 76}\n')


if __name__ == '__main__':
    main(parser.parse_args())
