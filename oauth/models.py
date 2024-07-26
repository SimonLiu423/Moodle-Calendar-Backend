"""Models for the oauth app."""
from django.db import models


class UserOAuth(models.Model):
    """Model for storing user's oauth credentials."""
    user_id = models.IntegerField()
    oauth_credentials = models.FileField(upload_to='tokens')

    def __str__(self):
        return f"{self.user_id}"
