from django.urls import path
from rankingsafa.views import *
urlpatterns = [
    path('inicio/', mostrar_inicio, name='inicio'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('upload-json/', upload_json, name='upload_json'),

    # CRUD Categorías (administración)
    path('categorias/', categoria_list, name='categoria_list'),
    path('categorias/crear/', categoria_create, name='categoria_create'),
    path('categorias/<int:pk>/editar/', categoria_update, name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', categoria_delete, name='categoria_delete'),

    # Vista pública de categorías
    path('categorias-explorar/', categoria_public_list, name='categoria_public_list'),
    path('categorias/<int:code>/juegos/', categoria_games, name='categoria_games'),
    path('juego/<int:code>/', game_detail, name='game_detail'),
]