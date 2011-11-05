from django.contrib.auth.models import User
from django.db import models

class TokenCollection(models.Model):
    user = models.ForeignKey(User)
    pickled_tokens = models.TextField(db_index=False)
