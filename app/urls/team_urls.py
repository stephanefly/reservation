from django.urls import path
from ..views import template_to_do, change_status, upload_image

urlpatterns = [
    path('template/', template_to_do, name='template_to_do'),
    path('change-status/<int:pk>/', change_status, name='change_status'),
    path('upload/<int:event_id>/', upload_image, name='upload_image'),

]
