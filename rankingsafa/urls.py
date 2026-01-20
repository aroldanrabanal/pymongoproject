from django.urls import path
from rankingsafa.views import *
urlpatterns = [
    path('inicio/', mostrar_inicio, name='inicio'),
]