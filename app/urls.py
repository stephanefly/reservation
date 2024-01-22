from django.urls import path
from .views import demande_devis, remerciement

urlpatterns = [
    path('', demande_devis, name='demande_devis'),
    path('remerciement', remerciement, name='remerciement'),
]
