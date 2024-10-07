from django.urls import path
from ..views import template_to_do, change_status

urlpatterns = [
    path('template/', template_to_do, name='template_to_do'),
    path('change-status/<int:pk>/', change_status, name='change_status'),
]
