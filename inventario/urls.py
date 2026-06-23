from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogo_tenant, name='catalogo'),
    path('reservar/', views.procesar_reserva, name='procesar_reserva'),
]