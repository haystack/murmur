from django.db import models
from django.contrib.auth.models import User
from oauth2client.django_orm import FlowField, CredentialsField
from http_handler.settings import AUTH_USER_MODEL
 
class FlowModel(models.Model):
    id = models.ForeignKey(AUTH_USER_MODEL, primary_key=True)
    flow = FlowField()
 
 
class CredentialsModel(models.Model):
    id = models.ForeignKey(AUTH_USER_MODEL, primary_key=True)
    credential = CredentialsField()