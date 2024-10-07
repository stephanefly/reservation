from django.urls import path
from ..views import (
    lst_cost, create_cost, info_cost, edit_cost, delete_cost
)

urlpatterns = [
    path('lst/', lst_cost, name='lst_cost'),
    path('create/', create_cost, name='create_cost'),
    path('info/<int:id>/', info_cost, name='info_cost'),
    path('edit/<int:id>/', edit_cost, name='edit_cost'),
    path('delete/<int:id>/', delete_cost, name='delete_cost'),
]
