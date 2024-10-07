from django.urls import path
from ..views import logging_client, choix_client, edit_horaire, edit_comment, edit_text, edit_template, relance_espace_client

urlpatterns = [
    path('', logging_client, name='logging_client'),
    path('<int:id>/<str:token>/', choix_client, name='choix_client'),
    path('edit_horaire/<int:event_id>/', edit_horaire, name='edit_horaire'),
    path('edit_comment/<int:event_id>/', edit_comment, name='edit_comment'),
    path('edit_text/<int:event_id>/', edit_text, name='edit_text'),
    path('edit_template/<int:event_id>/', edit_template, name='edit_template'),
    path('relance/<int:event_id>/', relance_espace_client, name='relance_espace_client'),
]
