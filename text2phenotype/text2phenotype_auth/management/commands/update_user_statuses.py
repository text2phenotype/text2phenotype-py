from django.core.management.base import BaseCommand

from text2phenotype.common.log import operations_logger
from text2phenotype.constants.environment import Environment
from text2phenotype.text2phenotype_auth.models.text2phenotype_user import Text2phenotypeUser
from text2phenotype.text2phenotype_auth.okta.client import OktaClient
from text2phenotype.text2phenotype_auth.okta.constants import OktaConstants


class Command(BaseCommand):
    help = 'Get statuses from Okta and update them in the database'

    def handle(self, *args, **options):
        client = OktaClient(
            Environment.OKTA_TENANT_URL.value,
            Environment.OKTA_API_TOKEN.value,
        )
        users = client.get_all_users()
        for status in OktaConstants.UserStatus:
            login_users = [user['profile']['login'] for user in filter(lambda x: x['status'] == status, users)]
            Text2phenotypeUser.objects.filter(sub__in=login_users).update(status=status)
        operations_logger.info('User statuses were updated successfully!')
