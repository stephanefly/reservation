from django.urls import path
from ..views import (
    comptabilite
)

urlpatterns = [
    path('lst_compta/', comptabilite, name='comptabilite'),
]
