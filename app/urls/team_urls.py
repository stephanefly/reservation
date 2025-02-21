from django.urls import path
from ..views import template_to_do, change_status, upload_image, view_image, team_post_presta,team_planning, media_collected, calendar

urlpatterns = [
    path('template/', template_to_do, name='template_to_do'),
    path('change-status/<int:pk>/', change_status, name='change_status'),
    path('upload_image/<int:event_id>/', upload_image, name='upload_image'),
    path('view-image/<int:event_id>/', view_image, name='view_image'),
    path('post-presta/', team_post_presta, name='team_post_presta'),
    path('planning/', team_planning, name='team_planning'),
    path('calendar/', calendar, name='calendar'),
    path('media_collected/<int:event_id>/', media_collected, name='media_collected'),

]
