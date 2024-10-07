from django.urls import path
from ..views import post_presta, presta_fini, update_post_presta_status

urlpatterns = [
    path('', post_presta, name='post_presta'),
    path('presta_fini/<int:event_id>/', presta_fini, name='presta_fini'),
    path('<int:post_presta_id>/<str:action>/', update_post_presta_status, name='update_post_presta_status'),

]
