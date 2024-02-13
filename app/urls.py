from django.urls import path
from .views import demande_devis, remerciement, lst_devis, confirmation, info_event, update_event, generate_pdf, \
    envoi_mail_devis, preparation_presta, confirmation_envoi_mail
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', demande_devis, name='demande_devis'),
    path('remerciement', remerciement, name='remerciement'),
    path('confirmation/', confirmation, name='confirmation'),
    path("login/", auth_views.LoginView.as_view(template_name="app\login.html"), name="login"),
    path('lst_devis', lst_devis, name='lst_devis'),
    path('info-event/<int:id>/', info_event, name='info_event'),
    path('event/update/<int:id>/', update_event, name='update_event'),
    path('generate-pdf/<int:event_id>/', generate_pdf, name='generate_pdf'),
    path('confirmation_envoi_mail/<int:event_id>/', confirmation_envoi_mail, name='confirmation_envoi_mail'),
    path('envoi_mail_devis/<int:event_id>/', envoi_mail_devis, name='envoi_mail_devis'),
    path('preparation_presta/', preparation_presta, name='preparation_presta'),
]
