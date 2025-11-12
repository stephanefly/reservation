from django.urls import path
from ..views import tarifs, brochure  # Assurez-vous que la vue 'tarifs' est bien définie

urlpatterns = [
    path('', tarifs, name='tarifs'),
    path('brochure/', brochure, name='brochure'),
]
