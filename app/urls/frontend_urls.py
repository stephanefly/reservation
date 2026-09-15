from django.urls import path
from ..views import demande_devis, remerciement, confirmation
from django.contrib.auth import views as auth_views
from app.login_views import login_redirect

urlpatterns = [
    path('login/redirect/', login_redirect, name='login_redirect'),
    path('', demande_devis, name='demande_devis'),
    path('remerciement/', remerciement, name='remerciement'),
    path('confirmation/', confirmation, name='confirmation'),
    path("login/", auth_views.LoginView.as_view(template_name="app/backend/login.html"), name="login"),
]
