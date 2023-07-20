from typing import List

import django.core.exceptions
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser
from django.db import (
    models,
    transaction,
)
from django.utils.functional import cached_property

from text2phenotype.common.log import operations_logger
from text2phenotype.text2phenotype_auth.okta.constants import OktaConstants

from .destination import Destination
from .email import EmailAddress
from .text2phenotype_base import IDBase
from .user_session import UserSession
from .text2phenotype_group import Text2phenotypeGroup


def make_unusable_password():
    return make_password(None)


class VisibleUsersManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Text2phenotypeUser(AbstractBaseUser, IDBase):
    # Foreign Key Relations
    destination = models.ForeignKey(Destination, models.SET_NULL, related_name="users", null=True, blank=True)

    # groups = models.ManyToManyField('Group', related_name='users')

    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)

    organization = models.CharField(max_length=255, blank=True, null=True)

    last_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    sub = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Okta
    # Okta User Status
    status = models.CharField(
        max_length=16,
        choices=[(item.value, item.value) for item in OktaConstants.UserStatus],
        default=OktaConstants.UserStatus.ACTIVE.value,
    )

    # count unsuccessful login attempts: 5 max before lock-out
    login_attempt_count = models.IntegerField(default=0)

    access_token = models.TextField(null=True, blank=True)
    access_expiry = models.DateTimeField(null=True, blank=True)

    password = models.CharField(max_length=128, default=make_unusable_password)
    text2phenotype_provisioned = models.BooleanField(default=True)

    is_deleted = models.BooleanField(default=False, null=False, blank=False)
    is_annotation_tool_visible = models.BooleanField(default=True, null=False, blank=True)

    objects = models.Manager()
    visible = VisibleUsersManager()

    USERNAME_FIELD = 'sub'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.primary_email

    @property
    def is_active(self):
        return self.status == OktaConstants.UserStatus.ACTIVE

    @property
    def login_attempts_exceeded(self):
        return self.login_attempt_count >= 5

    @cached_property
    def primary_email(self):
        try:
            email = self.emails.get(primary=True)
        except django.core.exceptions.ObjectDoesNotExist:
            return ''
        else:
            return email.email

    @cached_property
    def username(self):
        return self.primary_email

    def get_full_name(self):
        full_name = f'{self.first_name or ""} {self.last_name or ""}'.strip()
        return full_name if full_name else self.primary_email

    def get_short_name(self):
        return self.primary_email or self.get_full_name()

    @transaction.atomic
    def set_null_related(self):
        self.emails.all().delete()
        self.text2phenotype_groups.clear()
        UserSession.objects.filter(user=self).delete()

    @classmethod
    @transaction.atomic
    def erase_relations(cls) -> List[int]:
        """Removes relations between deleted users and other stuff"""

        deleted_users_ids = cls.objects.filter(is_deleted=True) \
                                       .values_list('pk', flat=True)

        operations_logger.info(
            f'Clean up deleted users and their relations. '
            f'Founded {len(deleted_users_ids)} users marked as deleted.')

        EmailAddress.objects.filter(user_id__in=deleted_users_ids).delete()
        UserSession.objects.filter(user_id__in=deleted_users_ids).delete()
        Text2phenotypeGroup.users.through.objects.filter(text2phenotypeuser_id__in=deleted_users_ids) \
                                        .delete()

        return deleted_users_ids
