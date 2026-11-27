from django.urls import path

from . import views

app_name = "newsletter_public"
urlpatterns = [
    path("ouverture/<uuid:token>.gif", views.opened, name="open"),
    path("lien/<uuid:token>/<str:signature>/", views.click, name="click"),
    path("desabonnement/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
]
