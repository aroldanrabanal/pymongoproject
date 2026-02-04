from django.shortcuts import render, redirect, get_object_or_404
from rankingsafa.forms import RegisterForm, LoginForm, UploadJSONForm, CategoriaForm, ReviewForm
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Videojuego, Categoria, Review
import json

# Helpers para categorías: nombre y color determinista por código
def _build_categoria_maps():
    categorias = Categoria.objects.all()
    name_map = {c.code: c.name for c in categorias}
    palette = ['is-primary', 'is-link', 'is-info', 'is-success', 'is-warning', 'is-danger', 'is-dark']
    color_map = {c.code: palette[c.code % len(palette)] for c in categorias}
    return name_map, color_map

# Create your views here.
def mostrar_inicio(request):
    videojuegos = Videojuego.objects.all()
    name_map, color_map = _build_categoria_maps()
    for v in videojuegos:
        cats = getattr(v, 'category', []) or []
        v.cat_tags = [
            {
                'name': name_map.get(code, f'Cat. {code}'),
                'color': color_map.get(code, 'is-dark')
            }
            for code in cats
        ]
    return render(request, 'inicio.html', {'videojuegos': videojuegos})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            auth_login(request, user)
            return redirect('inicio')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('inicio')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('inicio')

@staff_member_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@staff_member_required
def upload_json(request):
    if request.method == 'POST':
        form = UploadJSONForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = request.FILES['json_file']
            data = json.load(json_file)

            # Procesar categorías
            if 'categorias' in data:
                for cat_data in data['categorias']:
                    # Mapear campos de JSON a Modelo
                    # JSON: id, nombre, descripcion, imagen_url
                    # Modelo: code (int), name, desc, image
                    try:
                        code = int(cat_data['id'].split('_')[1])
                    except (IndexError, ValueError):
                        code = 0
                    
                    image_url = cat_data.get('imagen_url', '') or cat_data.get('image', '')
                    
                    existing = Categoria.objects.filter(code=code)
                    if existing.exists():
                        existing.update(
                            name=cat_data['nombre'],
                            desc=cat_data['descripcion'],
                            image=image_url
                        )
                    else:
                        Categoria.objects.create(
                            code=code,
                            name=cat_data['nombre'],
                            desc=cat_data['descripcion'],
                            image=image_url
                        )

            # Procesar videojuegos
            if 'videojuegos' in data:
                for game_data in data['videojuegos']:
                    # JSON: id, nombre, desarrollador, publisher, categorias, descripcion, fecha_lanzamiento, plataformas, imagen_url, precio_actual, clasificacion_edad, duracion_aproximada, multijugador
                    # Modelo Videojuego: code, name, desc, category (ArrayField), image
                    try:
                        code = int(game_data['id'].split('_')[1])
                    except (IndexError, ValueError):
                        code = 0

                    # Convertir categorías string (id) a int (code) si es necesario
                    category_codes = []
                    for cat_id in game_data.get('categorias', []):
                        try:
                            cat_code = int(cat_id.split('_')[1])
                            category_codes.append(cat_code)
                        except (IndexError, ValueError):
                            pass

                    existing_game = Videojuego.objects.filter(code=code)
                    game_fields = {
                        'name': game_data['nombre'],
                        'desc': game_data['descripcion'],
                        'category': category_codes,
                        'image': game_data.get('imagen_url', ''),
                        'developer': game_data.get('desarrollador', ''),
                        'publisher': game_data.get('publisher', ''),
                        'release_date': game_data.get('fecha_lanzamiento'),
                        'platforms': game_data.get('plataformas', []),
                        'price': game_data.get('precio_actual', 0.0),
                        'age_rating': game_data.get('clasificacion_edad', ''),
                        'duration': game_data.get('duracion_aproximada', 0),
                        'multiplayer': game_data.get('multijugador', False),
                    }
                    if existing_game.exists():
                        existing_game.update(**game_fields)
                    else:
                        Videojuego.objects.create(code=code, **game_fields)
            
            return redirect('inicio')
    else:
        form = UploadJSONForm()
    return render(request, 'upload_json.html', {'form': form})

@staff_member_required
def categoria_list(request):
    categorias = Categoria.objects.all()
    form = CategoriaForm()
    return render(request, 'categoria_list.html', {'categorias': categorias, 'form': form})

@staff_member_required
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            try:
                # Generar código automático: siguiente al máximo existente
                last_code = Categoria.objects.order_by('-code').values_list('code', flat=True).first()
                next_code = (last_code or 0) + 1
                Categoria.objects.create(
                    code=next_code,
                    name=cleaned['name'],
                    desc=cleaned['desc'],
                    image=cleaned.get('image', '')
                )
                messages.success(request, 'Categoría creada correctamente.')
                return redirect('categoria_list')
            except Exception as e:
                messages.error(request, 'Ocurrió un error al crear la categoría.')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        return redirect('categoria_list')
    # Ya no renderizamos categoria_form.html

@staff_member_required
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        # Evita cambios de PK y asegura persistencia en Mongo
        if 'code' in form.fields:
            form.fields['code'].disabled = True
        if form.is_valid():
            cleaned = form.cleaned_data
            try:
                # Actualización directa para garantizar que se guarde en MongoDB con managed=False
                Categoria.objects.filter(pk=pk).update(
                    name=cleaned.get('name', categoria.name),
                    desc=cleaned.get('desc', categoria.desc),
                    image=cleaned.get('image', categoria.image)
                )
                messages.success(request, 'Categoría actualizada correctamente.')
                return redirect('categoria_list')
            except Exception as e:
                messages.error(request, 'Ocurrió un error al actualizar la categoría.')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        return redirect('categoria_list')
    # Ya no renderizamos categoria_form.html

@staff_member_required
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoría eliminada correctamente.')
        except Exception:
            messages.error(request, 'Ocurrió un error al eliminar la categoría.')
        return redirect('categoria_list')
    # Si alguien intenta entrar por GET, redirigimos al listado
    return redirect('categoria_list')

def categoria_public_list(request):
    categorias = Categoria.objects.all()
    return render(request, 'categoria_cards.html', {'categorias': categorias})

# Listado de juegos por categoría (vista pública)
def categoria_games(request, code):
    categoria = get_object_or_404(Categoria, code=code)
    # Videojuego.category es un ArrayField de códigos de categoría.
    # En MongoDB, (campo = valor) actúa como búsqueda de pertenencia en arrays.
    videojuegos = Videojuego.objects.filter(category=code)
    name_map, color_map = _build_categoria_maps()
    for v in videojuegos:
        cats = getattr(v, 'category', []) or []
        v.cat_tags = [
            {
                'name': name_map.get(c, f'Cat. {c}'),
                'color': color_map.get(c, 'is-dark')
            }
            for c in cats
        ]
    context = {
        'categoria': categoria,
        'videojuegos': videojuegos,
    }
    return render(request, 'categoria_games.html', context)

def game_detail(request, code):
    juego = get_object_or_404(Videojuego, code=code)
    reviews = Review.objects.filter(code=code).order_by('-reviewDate')
    
    name_map, color_map = _build_categoria_maps()
    cats = getattr(juego, 'category', []) or []
    juego.cat_tags = [
        {
            'name': name_map.get(c, f'Cat. {c}'),
            'color': color_map.get(c, 'is-dark')
        }
        for c in cats
    ]
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para dejar una review.')
            return redirect('login')
            
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Generar serie automática para la review del juego
            last_review = Review.objects.filter(code=code).order_by('-serie').first()
            next_serie = (last_review.serie + 1) if last_review else 1
            
            # Crear review. Como es managed=False y Mongo, usamos .create() o .save()
            Review.objects.create(
                code=code,
                serie=next_serie,
                user=request.user.username,
                rating=form.cleaned_data['rating'],
                comentary=form.cleaned_data['comentary']
            )
            messages.success(request, 'Review añadida correctamente.')
            return redirect('game_detail', code=code)
    else:
        form = ReviewForm()
        
    return render(request, 'game_detail.html', {
        'juego': juego,
        'reviews': reviews,
        'form': form
    })