from django.db import models
from text2phenotype.text2phenotype_auth.models.text2phenotype_base import IDBase


class Destination(IDBase):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    internal = models.BooleanField(default=False)
