from django.urls import path
from .views import demande_devis, remerciement, info_lst_devis, confirmation, info_event, update_event, generate_pdf

urlpatterns = [
    path('', demande_devis, name='demande_devis'),
    path('remerciement', remerciement, name='remerciement'),
    path('lst_devis', info_lst_devis, name='info_lst_devis'),
    path('confirmation/', confirmation, name='confirmation'),
    path('info-event/<int:id>/', info_event, name='info_event'),
    path('event/update/<int:id>/', update_event, name='update_event'),
    path('generate-pdf/<int:event_id>/', generate_pdf, name='generate_pdf'),
]
