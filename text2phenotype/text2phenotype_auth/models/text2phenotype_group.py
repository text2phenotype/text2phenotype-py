from django.db import models

from text2phenotype.text2phenotype_auth.okta.auth_constant import Applications
from text2phenotype.text2phenotype_auth.models.text2phenotype_base import IDBase


class IntegrationPortalGroupManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().filter(
            application=Applications.INTEGRATION_PORTAL.value)

    def get_or_create(self, *args, **kwargs):
        kwargs.update(application=Applications.INTEGRATION_PORTAL.value)
        return super().get_or_create(*args, **kwargs)


class SandsGroupManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().filter(
            application=Applications.SANDS.value)

    def get_or_create(self, *args, **kwargs):
        kwargs.update(application=Applications.SANDS.value)
        return super().get_or_create(*args, **kwargs)


class Text2phenotypeGroup(IDBase):
    """
    This Model tracks permission groups/roles.
    """
    objects = models.Manager()
    integration_portal = IntegrationPortalGroupManager()
    sands = SandsGroupManager()

    # Fields
    name = models.CharField(max_length=50)
    application = models.IntegerField(choices=[[x.value, x.value] for x in Applications])
    okta_id = models.CharField(max_length=50, blank=True, null=True)

    # Relations
    users = models.ManyToManyField('Text2phenotypeUser', related_name='text2phenotype_groups')

    class Meta:
        unique_together = (('name', 'application'),)
