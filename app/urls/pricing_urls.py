from django.urls import path
from ..views import tarifs  # Assurez-vous que la vue 'tarifs' est bien définie

urlpatterns = [
    path('', tarifs, name='tarifs'),
]
