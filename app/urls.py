from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # FRONTEND
    path('', demande_devis, name='demande_devis'),
    path('remerciement', remerciement, name='remerciement'),
    path('confirmation/', confirmation, name='confirmation'),
    path("login/", auth_views.LoginView.as_view(template_name="app/backend/login.html"), name="login"),
    # BACKEND DEVIS
    path('backend/lst_devis/', lst_devis, name='lst_devis'),
    path('backend/lst_cost/', lst_cost, name='lst_cost'),
    path('backend/info-event/<int:id>/', info_event, name='info_event'),
    path('backend/event/update/<int:id>/', update_event, name='update_event'),
    path('backend/generate-pdf/<int:event_id>/', generate_pdf, name='generate_pdf'),
    path('backend/validation_devis/<int:id>/', validation_devis, name='validation_devis'),
    path('backend/confirmation_del_devis/<int:event_id>/', confirmation_del_devis, name='confirmation_del_devis'),
    path('backend/del_devis/<int:id>/', del_devis, name='del_devis'),
    path('backend/refused_devis/<int:id>/', refused_devis, name='refused_devis'),
    path('backend/confirmation_envoi_mail/<int:event_id>/', confirmation_envoi_mail, name='confirmation_envoi_mail'),
    path('backend/envoi_mail_devis/<int:event_id>/', envoi_mail_devis, name='envoi_mail_devis'),
    # BACKEND COST
    path('backend/create_cost/', create_cost, name='create_cost'),
    path('backend/info_cost/<int:id>/', info_cost, name='info_cost'),
    path('backend/edit_cost/<int:id>/', edit_cost, name='edit_cost'),
    path('backend/delete_cost/<int:id>/', delete_cost, name='delete_cost'),
    # BACKEND GRAPH
    path('backend/graph/', graph, name='graph'),
    path('backend/graph_cost/', graph_cost, name='graph_cost'),
    path('backend/graph_cost_pie/', graph_cost_pie, name='graph_cost_pie'),
    # BACKEND PLANNING
    path('backend/generete_planning/', generete_planning, name='generete_planning'),
    # BACKEND TACHES PLANIFIES
    path('plannif_maj_event/', plannif_maj_event, name='plannif_maj_event'),

]

