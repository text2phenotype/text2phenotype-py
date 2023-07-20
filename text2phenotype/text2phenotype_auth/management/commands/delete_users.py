from django.core.management.base import BaseCommand
from text2phenotype.text2phenotype_auth.models.text2phenotype_user import Text2phenotypeUser


class Command(BaseCommand):
    help = 'Deletes users marked as is_deleted from db'

    def handle(self, *args, **options):
        Text2phenotypeUser.objects.filter(is_deleted=True).delete()
