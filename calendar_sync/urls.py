"""URLs for the calendar_sync app."""
from django.urls import path

from . import views

urlpatterns = [
    path('sync/', views.calendar_sync, name='sync'),
]
