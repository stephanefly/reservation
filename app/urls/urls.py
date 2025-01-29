from django.urls import path, include

from ..views import tableau_de_bord, post_presta, relance_avis_client, presta_fini, update_post_presta_status, \
    desabonner, action_once, track_devis
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('app.urls.frontend_urls')),

    path('backend/', tableau_de_bord, name='tableau_de_bord'),

    path('backend/post_presta/', include('app.urls.post_presta_urls')),
    path('backend/info-event/', include('app.urls.info_event_urls')),
    path('backend/cost/', include('app.urls.cost_urls')),
    path('backend/graph/', include('app.urls.graph_urls')),


    path('espace_client/', include('app.urls.espace_clients_urls')),
    path('team/', include('app.urls.team_urls')),
    path('tarifs/', include('app.urls.pricing_urls')),

    path('desabonner/<str:token>', desabonner, name='desabonner'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # URL de déconnexion

    path('backend/action_once', action_once, name='action_once'),
    path('track_devis/<uuid:uuid>/', track_devis, name='track_devis'),
]
