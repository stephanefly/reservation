from django.urls import path
from .views import demande_devis, remerciement, info_lst_devis

urlpatterns = [
    path('', demande_devis, name='demande_devis'),
    path('remerciement', remerciement, name='remerciement'),
    path('lst_devis', info_lst_devis, name='info_lst_devis'),
]
