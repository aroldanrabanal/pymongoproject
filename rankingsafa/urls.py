from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rankingsafa import views  # tus vistas personalizadas
from rankingsafa.views import *

urlpatterns = [
    # Página de inicio
    path('inicio/', views.mostrar_inicio, name='inicio'),

    # Autenticación (usamos las vistas por defecto de Django)
    # path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),

    # Registro (vamos a crear nuestra propia vista)
    path('register/', views.register, name='register'),

    # Opcional: reset de contraseña (si lo quieres después)
    # path('password_reset/', ... )
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

    # CRUD Videojuegos (administración)
    path('juegos-admin/', juego_list, name='juego_list'),
    path('juegos-admin/crear/', juego_create, name='juego_create'),
    path('juegos-admin/<int:pk>/editar/', juego_update, name='juego_update'),
    path('juegos-admin/<int:pk>/eliminar/', juego_delete, name='juego_delete'),

    # Vista pública de categorías
    path('categorias-explorar/', categoria_public_list, name='categoria_public_list'),
    path('categorias/<int:code>/juegos/', categoria_games, name='categoria_games'),

    # Listado y detalle de juegos
    path('juegos/', games_list, name='games_list'),
    path('juego/<int:code>/', game_detail, name='game_detail'),

    # Reseñas
    path('juego/<int:game_code>/review/<int:serie>/editar/', review_edit, name='review_edit'),
    path('juego/<int:game_code>/review/<int:serie>/eliminar/', review_delete, name='review_delete'),

    # Rankings
    path('rankings/', rankings_home, name='rankings_home'),
    path('rankings/categoria/<int:category_code>/', ranking_categoria_global, name='ranking_categoria_global'),
    path('rankings/categoria/<int:category_code>/crear/', ranking_crear, name='ranking_crear'),
    path('rankings/categoria/<int:category_code>/eliminar/', ranking_delete, name='ranking_delete'),

    # Usuarios
    path('usuarios/', user_list, name='user_list'),
    path('usuarios/<int:user_id>/eliminar/', user_delete, name='user_delete'),
    path('usuarios/<int:user_id>/toggle-staff/', user_toggle_staff, name='user_toggle_staff'),
    path('usuarios/<int:user_id>/toggle-role/', user_toggle_role, name='user_toggle_role'),
]