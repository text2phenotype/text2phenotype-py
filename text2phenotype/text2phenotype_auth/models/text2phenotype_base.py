import json
import uuid

from django.db import models
from django.core.exceptions import ValidationError

from text2phenotype.common.log import operations_logger


def generate_uuid():
    return uuid.uuid4().hex


class IDBase(models.Model):
    uuid = models.CharField(default=generate_uuid, max_length=32, db_index=True)  # id for URLs
    id = models.BigAutoField(primary_key=True, editable=False)  # primary key

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        try:
            uuid.UUID(self.uuid)
        except ValueError:
            raise ValidationError('Invalid `uuid` value: badly formed '
                                  'hexadecimal UUID string')

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)


class VisibleObectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Text2phenotypeBase(IDBase):
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    archived = models.BooleanField(default=False)

    objects = models.Manager()
    visible = VisibleObectManager()

    class Meta:
        abstract = True
        ordering = ['created_at']

    @property
    def class_name(self):
        return self.__class__.__name__

    def save(self, force_insert=False, force_update=False, **kwargs):

        # this attribute is only present if saved from the view function
        if hasattr(self, 'data'):
            operations_logger.debug(f'obj.data={self.data}')
            for f in self._meta.fields:
                # never update these fields through the view
                if f.name in ('created_at', 'modified_at',
                              'text2phenotype_id', 'id', 'uuid'):
                    continue

                if f.name in self.data.keys():
                    value = self.data[f.name]
                    if value in ['true', 'false']:
                        setattr(self, f.name, json.loads(value))
                    elif not value and isinstance(f, (models.DateField, models.DateTimeField)):
                        # This is workaround for "date" fields. '' for these fields -> ValidationError
                        setattr(self, f.name, None)
                    elif value:
                        setattr(self, f.name, value)
                else:
                    if type(f) == models.NullBooleanField and getattr(self, f.name):
                        setattr(self, f.name, False)
                    elif type(f) == models.CharField:
                        setattr(self, f.name, '')
                    elif type(f) == models.DateTimeField:
                        setattr(self, f.name, None)

        if not (force_insert or force_update):
            try:
                self.full_clean()
            except ValidationError as e:
                for k in e.message_dict.keys():
                    f = self._meta.get_field(k)
                    if type(f) == models.CharField:
                        setattr(self, k, '')
                    else:
                        setattr(self, k, None)

        models.Model.save(self, force_insert, force_update, **kwargs)
