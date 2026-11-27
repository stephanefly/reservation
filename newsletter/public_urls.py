from django.urls import path, re_path

from . import views
from .image_storage import IMAGE_NAME

app_name = "newsletter_public"
urlpatterns = [
    re_path(rf"^image/(?P<filename>{IMAGE_NAME})/$", views.public_image, name="image"),
    path("ouverture/<uuid:token>.gif", views.opened, name="open"),
    path("lien/<uuid:token>/<str:signature>/", views.click, name="click"),
    path("desabonnement/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
]
