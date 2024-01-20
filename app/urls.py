from django.urls import path
from .views import demande_devis

urlpatterns = [
    path('', demande_devis, name='demande_devis'),
]
