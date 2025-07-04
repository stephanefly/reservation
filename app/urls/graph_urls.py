from django.urls import path
from ..views import graph, graph_cost, graph_cost_pie, graph_potentiel, cycle_strategique_view

urlpatterns = [
    path('', graph, name='graph'),
    path('cost/', graph_cost, name='graph_cost'),
    path('cost/pie/', graph_cost_pie, name='graph_cost_pie'),
    path('potentiel', graph_potentiel, name='graph_potentiel'),
    path('cycle-strategique/', cycle_strategique_view, name='cycle_strategique'),
]
