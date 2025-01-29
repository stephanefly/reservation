from django.urls import path
from ..views import (
    lst_devis, info_event, update_event, generate_devis_pdf,
    generate_facture_pdf, confirmation_val_devis, confirmation_del_devis,
    del_devis, refused_devis, confirmation_envoi_mail, envoi_mail_devis, rappel_devis_client,
prolongation_devis_client, phonebooth_offert_devis_client, last_chance_devis_client
)

urlpatterns = [
    path('lst/', lst_devis, name='lst_devis'),
    path('<int:id>/', info_event, name='info_event'),
    path('event/update/<int:id>/', update_event, name='update_event'),
    path('generate-pdf/<int:event_id>/', generate_devis_pdf, name='generate_devis_pdf'),
    path('generate-facture-pdf/<int:event_id>/', generate_facture_pdf, name='generate_facture_pdf'),
    path('confirmation/val/<int:id>/', confirmation_val_devis, name='confirmation_val_devis'),
    path('confirmation/del/<int:event_id>/', confirmation_del_devis, name='confirmation_del_devis'),
    path('del/<int:id>/', del_devis, name='del_devis'),
    path('refused/<int:id>/', refused_devis, name='refused_devis'),
    path('envoi-mail/<int:event_id>/', envoi_mail_devis, name='envoi_mail_devis'),
    path('confirmation/envoi-mail/<int:event_id>/', confirmation_envoi_mail, name='confirmation_envoi_mail'),
    path('rappel_devis_client/<int:event_id>/', rappel_devis_client, name='rappel_devis_client'),
    path('prolongation_devis_client/<int:event_id>/', prolongation_devis_client, name='prolongation_devis_client'),
    path('phonebooth_offert_devis_client/<int:event_id>/', phonebooth_offert_devis_client, name='phonebooth_offert_devis_client'),
    path('last_chance_devis_client/<int:event_id>/', last_chance_devis_client, name='last_chance_devis_client'),
]
