"""Admin for the oauth app."""
from django.contrib import admin

from .models import UserOAuth

admin.site.register(UserOAuth)
