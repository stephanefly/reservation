from django.urls import path, include
from ..views import tableau_de_bord, post_presta, relance_avis_client, presta_fini, update_post_presta_status, \
    desabonner

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

    path('desabonner/<int:event_id>', desabonner, name='desabonner'),

]
