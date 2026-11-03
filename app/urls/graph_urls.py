from django.urls import path
from ..views.email_stats_views import graph_email_stats
from ..views.commercial_stats_views import graph_commercial_stats
from ..views.email_delivery_views import graph_email_delivery
from ..views import graph, graph_cost, graph_cost_pie, graph_potentiel, cycle_strategique_view

urlpatterns = [
    path('email-delivery/', graph_email_delivery, name='graph_email_delivery'),
    path('commercial/', graph_commercial_stats, name='graph_commercial_stats'),
    path('emails/', graph_email_stats, name='graph_email_stats'),
    path('', graph, name='graph'),
    path('cost/', graph_cost, name='graph_cost'),
    path('cost/pie/', graph_cost_pie, name='graph_cost_pie'),
    path('potentiel', graph_potentiel, name='graph_potentiel'),
    path('cycle-strategique/', cycle_strategique_view, name='cycle_strategique'),
]

