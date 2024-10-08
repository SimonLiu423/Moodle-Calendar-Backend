"""URLs for the oauth app."""
from django.urls import path

from . import views

urlpatterns = [
    path('status/', views.status, name='status'),
    path('bind/', views.bind, name='bind'),
    path('callback/', views.callback, name='callback'),
]
