from django.urls import path
from ..views import (post_presta, presta_fini, update_post_presta_status, relance_avis_client, send_media,
                     mark_client_unpaid, mark_client_paid, mark_members_unpaid, mark_members_paid, mark_sold_not_ok, mark_sold_ok,
                     mark_charge)

urlpatterns = [
    path('', post_presta, name='post_presta'),
    path('presta_fini/<int:event_id>/', presta_fini, name='presta_fini'),
    path('<int:post_presta_id>/<str:action>/', update_post_presta_status, name='update_post_presta_status'),
    path('relance/<int:event_id>/', relance_avis_client, name='relance_avis_client'),
    path('send_media/<int:event_id>/', send_media, name='send_media'),
    # mark_client_paid
    path("mark-unpaid/<int:event_id>/", mark_client_unpaid, name="mark_client_unpaid"),
    path("mark-paid/<int:event_id>/", mark_client_paid, name="mark_client_paid"),
    # mark_members_paid
    path("mark_members_unpaid/<int:event_id>/", mark_members_unpaid, name="mark_members_unpaid"),
    path("mark_members_paid/<int:event_id>/", mark_members_paid, name="mark_members_paid"),
    # mark_sold_ok
    path("mark_sold_not_ok/<int:event_id>/", mark_sold_not_ok, name="mark_sold_not_ok"),
    path("mark_sold_ok/<int:event_id>/", mark_sold_ok, name="mark_sold_ok"),
    # charges
    path("mark_charge/<int:event_id>/", mark_charge, name="mark_charge"),

]
