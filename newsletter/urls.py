from django.urls import path

from . import views

app_name = "newsletter"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("campagnes/", views.campaigns, name="campaigns"),
    path("campagnes/nouvelle/", views.create, name="create"),
    path("campagnes/<int:pk>/etape/<int:step>/", views.edit, name="edit"),
    path("campagnes/<int:pk>/confirmer/", views.confirm, name="confirm"),
    path("campagnes/<int:pk>/apercu/", views.preview, name="preview"),
    path("modeles/", views.templates, name="templates"),
    path("modeles/<int:pk>/", views.templates, name="template"),
    path("modeles/<int:pk>/dupliquer/", views.duplicate, name="duplicate"),
    path("historique/", views.history, name="history"),
    path("historique/<int:pk>/", views.detail, name="detail"),
    path("test/", views.smtp_test, name="test"),
    path("parametres/", views.configuration, name="settings"),
]
