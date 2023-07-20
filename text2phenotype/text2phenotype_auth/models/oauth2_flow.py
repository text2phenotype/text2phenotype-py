from django.db import models
from django.contrib.sessions.models import Session


class OAuth2Flow(models.Model):
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    session = models.OneToOneField(Session, primary_key=True,
                                   on_delete=models.CASCADE)
    state = models.TextField()
    nonce = models.TextField()
    redirect_url = models.CharField(blank=True, null=True, max_length=255)
