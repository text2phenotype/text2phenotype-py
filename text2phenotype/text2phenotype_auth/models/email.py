from django.db import models

from text2phenotype.text2phenotype_auth.models.text2phenotype_base import IDBase


class EmailAddress(IDBase):
    user = models.ForeignKey('Text2phenotypeUser', models.CASCADE, related_name='emails')
    email = models.EmailField(unique=True)
    primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.primary:
            # Enforce only one primary email per user
            self.user.emails.exclude(id=self.id).update(primary=False)

    def make_primary(self):
        """
        Mark this email address as the primary email address for the user and
        demote all others.
        """
        self.user.emails.all().update(primary=False)
        self.primary = True
        self.save()
