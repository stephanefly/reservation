from django.urls import path
from .views import demande_devis, remerciement, lst_devis, confirmation, info_event, update_event, generate_pdf, \
    envoi_mail_devis, preparation_presta, confirmation_envoi_mail, validation_devis, del_devis, confirmation_del_devis, \
    import_data_devis, refused_devis
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # FRONTEND
    path('', demande_devis, name='demande_devis'),
    path('remerciement', remerciement, name='remerciement'),
    path('confirmation/', confirmation, name='confirmation'),
    path("login/", auth_views.LoginView.as_view(template_name="app/login.html"), name="login"),
    # BACKEND
    path('backend/lst_devis/', lst_devis, name='lst_devis'),
    path('backend/info-event/<int:id>/', info_event, name='info_event'),
    path('backend/event/update/<int:id>/', update_event, name='update_event'),
    path('backend/generate-pdf/<int:event_id>/', generate_pdf, name='generate_pdf'),
    path('backend/validation_devis/<int:id>/', validation_devis, name='validation_devis'),
    path('backend/confirmation_del_devis/<int:event_id>/', confirmation_del_devis, name='confirmation_del_devis'),
    path('backend/del_devis/<int:id>/', del_devis, name='del_devis'),
    path('backend/refused_devis/<int:id>/', refused_devis, name='refused_devis'),
    path('backend/confirmation_envoi_mail/<int:event_id>/', confirmation_envoi_mail, name='confirmation_envoi_mail'),
    path('backend/envoi_mail_devis/<int:event_id>/', envoi_mail_devis, name='envoi_mail_devis'),
    path('backend/preparation_presta/', preparation_presta, name='preparation_presta'),
    path('backend/import_data_devis/', import_data_devis, name='import_data_devis'),
]
