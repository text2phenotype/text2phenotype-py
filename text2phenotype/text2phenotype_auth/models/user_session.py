from django.db import models
from django.contrib.sessions.models import Session


class UserSession(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)  # primary key
    user = models.ForeignKey('Text2phenotypeUser', models.CASCADE)
    session = models.ForeignKey(Session, models.CASCADE)


