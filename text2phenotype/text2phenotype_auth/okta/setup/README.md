Example usage of scripts:
( Scripts must be in root of this repo, not in scripts/ dir)

You can create a developer account here: https://developer.okta.com/

Google Oauth secrets are located at the following under "Text2phenotype Services" (Admin access required in Google):
  NonProd: https://console.developers.google.com/apis/credentials?project=oauth-access-non-prod&organizationId=109432028419
  Prod: https://console.developers.google.com/apis/credentials?project=oauth-access-prod&organizationId=109432028419

First the tenant setup:
  ( Currently there is an issue that GROUP_MEMBERSHIP_RULES must be enabled by Okta )

  python setup_okta_tenant.py --tenant_url https://dev-102918-admin.okta.com --api_token <token from Okta API> --google_client_id < Google oauth client ID>  > --google_client_secret < Google oauth secret associated with client id>

Then the customer setup:

  python setup_okta_customer.py --tenant_url https://dev-227502-admin.okta.com/ --api_token <token from Okta API> --env_name < arbitrary name like mdl-dev-alpha > --dns_name < URL of cluster like https://alpha.mdl-dev.in >

