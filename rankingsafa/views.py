from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rankingsafa.forms import RegisterForm, LoginForm, UploadJSONForm, CategoriaForm, VideojuegoForm, ReviewForm
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout, get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Videojuego, Categoria, Review, Ranking
from django.db.models import Count, Avg
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
    # Obtener juegos como lista
    videojuegos = list(Videojuego.objects.all())

    # Calcular estadísticas de reviews por código de juego en una sola consulta
    stats = Review.objects.values('code').annotate(
        reviews_count=Count('rating'),
        avg_rating=Avg('rating')
    )
    stats_map = {s['code']: s for s in stats}

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

        # Adjuntar estadísticas (por si no hay reviews, poner 0)
        stat = stats_map.get(v.code, {})
        v.reviews_count = stat.get('reviews_count', 0)
        v.avg_rating = round(stat.get('avg_rating') or 0, 1)

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
            # Usamos filter().delete() por consistencia con managed=False en MongoDB
            Categoria.objects.filter(pk=pk).delete()
            messages.success(request, 'Categoría eliminada correctamente.')
        except Exception:
            messages.error(request, 'Ocurrió un error al eliminar la categoría.')
        return redirect('categoria_list')
    # Si alguien intenta entrar por GET, redirigimos al listado
    return redirect('categoria_list')


@staff_member_required
def juego_list(request):
    juegos = Videojuego.objects.all().order_by('code')
    categorias = Categoria.objects.all()
    form = VideojuegoForm()
    return render(request, 'juego_list.html', {
        'juegos': juegos,
        'categorias': categorias,
        'form': form
    })


@staff_member_required
def juego_create(request):
    if request.method == 'POST':
        form = VideojuegoForm(request.POST)
        if form.is_valid():
            # Auto-increment code
            last_code = Videojuego.objects.order_by('-code').values_list('code', flat=True).first()
            next_code = (last_code or 0) + 1

            # Las categorías ya vienen como lista de enteros desde clean_category()
            category_codes = form.cleaned_data.get('category', [])

            # Las plataformas ya vienen como lista desde clean_platforms()
            platforms = form.cleaned_data.get('platforms', [])

            # Crear juego
            Videojuego.objects.create(
                code=next_code,
                name=form.cleaned_data['name'],
                desc=form.cleaned_data['desc'],
                image=form.cleaned_data.get('image', ''),
                developer=form.cleaned_data.get('developer', ''),
                publisher=form.cleaned_data.get('publisher', ''),
                release_date=form.cleaned_data.get('release_date'),
                category=category_codes,
                platforms=platforms,
                price=form.cleaned_data.get('price', 0),
                age_rating=form.cleaned_data.get('age_rating', ''),
                duration=form.cleaned_data.get('duration', 0),
                multiplayer=form.cleaned_data.get('multiplayer', False)
            )
            messages.success(request, 'Juego creado correctamente.')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
        return redirect('juego_list')
    return redirect('juego_list')


@staff_member_required
def juego_update(request, pk):
    juego = get_object_or_404(Videojuego, pk=pk)

    if request.method == 'POST':
        form = VideojuegoForm(request.POST, instance=juego)
        if form.is_valid():
            # Las categorías ya vienen como lista de enteros desde clean_category()
            category_codes = form.cleaned_data.get('category', [])

            # Las plataformas ya vienen como lista desde clean_platforms()
            platforms = form.cleaned_data.get('platforms', [])

            # Actualizar usando filter().update() por MongoDB managed=False
            Videojuego.objects.filter(pk=pk).update(
                name=form.cleaned_data['name'],
                desc=form.cleaned_data['desc'],
                image=form.cleaned_data.get('image', ''),
                developer=form.cleaned_data.get('developer', ''),
                publisher=form.cleaned_data.get('publisher', ''),
                release_date=form.cleaned_data.get('release_date'),
                category=category_codes,
                platforms=platforms,
                price=form.cleaned_data.get('price', 0),
                age_rating=form.cleaned_data.get('age_rating', ''),
                duration=form.cleaned_data.get('duration', 0),
                multiplayer=form.cleaned_data.get('multiplayer', False)
            )
            messages.success(request, 'Juego actualizado correctamente.')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
        return redirect('juego_list')
    return redirect('juego_list')


@staff_member_required
def juego_delete(request, pk):
    juego = get_object_or_404(Videojuego, pk=pk)

    if request.method == 'POST':
        # Usar filter().delete() por MongoDB managed=False
        Videojuego.objects.filter(pk=pk).delete()
        messages.success(request, 'Juego eliminado correctamente.')

    return redirect('juego_list')


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


def games_list(request):
    # Obtener todos los videojuegos
    videojuegos = Videojuego.objects.all()

    # Obtener filtros de la query string
    selected_categories = request.GET.getlist('category')  # Lista de códigos de categoría
    selected_platforms = request.GET.getlist('platform')  # Lista de plataformas

    # Aplicar filtros
    if selected_categories:
        # Convertir a enteros
        selected_categories = [int(c) for c in selected_categories if c.isdigit()]
        # Filtrar juegos que tengan al menos una de las categorías seleccionadas
        videojuegos = [v for v in videojuegos if any(cat in (v.category or []) for cat in selected_categories)]

    if selected_platforms:
        # Filtrar juegos que tengan al menos una de las plataformas seleccionadas
        videojuegos = [v for v in videojuegos if any(plat in (v.platforms or []) for plat in selected_platforms)]

    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.all()

    # Obtener todas las plataformas únicas
    all_platforms = set()
    for v in Videojuego.objects.all():
        if v.platforms:
            all_platforms.update(v.platforms)
    all_platforms = sorted(all_platforms)

    # Añadir tags de categorías a cada juego
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
        'videojuegos': videojuegos,
        'categorias': categorias,
        'all_platforms': all_platforms,
        'selected_categories': [int(c) for c in request.GET.getlist('category') if c.isdigit()],
        'selected_platforms': request.GET.getlist('platform'),
    }
    return render(request, 'games_list.html', context)


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
            if Review.objects.filter(code=code, user=request.user.username).exists():
                messages.error(request, 'Solo una review por usuario.')
            else:
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


@login_required
def review_edit(request, game_code, serie):
    review = get_object_or_404(Review, code=game_code, serie=serie)

    # Verificar que el usuario sea el autor
    if review.user != request.user.username:
        messages.error(request, 'No tienes permiso para editar esta reseña.')
        return redirect('game_detail', code=game_code)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            try:
                # Como Review es managed=False, usamos update directo
                Review.objects.filter(code=game_code, serie=serie).update(
                    rating=cleaned.get('rating', review.rating),
                    comentary=cleaned.get('comentary', review.comentary)
                )
                messages.success(request, 'Reseña actualizada correctamente.')
                return redirect('game_detail', code=game_code)
            except Exception:
                messages.error(request, 'Ocurrió un error al actualizar la reseña.')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        # Si alguien intenta entrar por GET, redirigimos al detalle del juego
        return redirect('game_detail', code=game_code)


# ========== RANKINGS ==========
def rankings_home(request):
    """Vista principal de rankings - muestra todas las categorías"""
    categorias = Categoria.objects.all()
    return render(request, 'rankings_home.html', {'categorias': categorias})


def ranking_categoria_global(request, category_code):
    """Ver el ranking global (promedio) de una categoría"""
    categoria = get_object_or_404(Categoria, code=category_code)

    # Obtener todos los juegos de esta categoría
    videojuegos = Videojuego.objects.filter(category=category_code)

    # Obtener todos los rankings de esta categoría
    rankings = Ranking.objects.filter(category=category_code)

    # Calcular puntuación promedio para cada juego
    # Sistema de puntos basado en posición: 1º lugar = más puntos
    game_scores = {}
    game_positions = {}  # Para rastrear las posiciones de cada juego

    for ranking in rankings:
        ranking_list = ranking.rankingList or []
        total_games = len(ranking_list)

        for idx, game_code in enumerate(ranking_list):
            # Puntos = (total_juegos - posición)
            # 1º lugar (idx=0) = total_games puntos
            # 2º lugar (idx=1) = total_games - 1 puntos, etc.
            points = total_games - idx

            if game_code not in game_scores:
                game_scores[game_code] = []
                game_positions[game_code] = []

            game_scores[game_code].append(points)
            game_positions[game_code].append(idx + 1)  # Posición (1-indexed)

    # Calcular promedio y ordenar
    game_rankings = []
    for juego in videojuegos:
        if juego.code in game_scores:
            scores = game_scores[juego.code]
            avg_score = sum(scores) / len(scores)
            avg_position = sum(game_positions[juego.code]) / len(game_positions[juego.code])

            game_rankings.append({
                'juego': juego,
                'score': round(avg_score, 2),
                'avg_position': round(avg_position, 1),
                'votes': len(scores)
            })

    # Ordenar por puntuación
    game_rankings.sort(key=lambda x: x['score'], reverse=True)

    context = {
        'categoria': categoria,
        'game_rankings': game_rankings,
        'total_rankings': rankings.count()
    }
    return render(request, 'ranking_global.html', context)


@login_required
def ranking_crear(request, category_code):
    """Crear o editar tu ranking de una categoría"""
    categoria = get_object_or_404(Categoria, code=category_code)

    # Obtener juegos de esta categoría
    videojuegos = list(Videojuego.objects.filter(category=category_code))

    # Verificar si el usuario ya tiene un ranking para esta categoría
    existing_ranking = Ranking.objects.filter(
        user=request.user.username,
        category=category_code
    ).first()

    if request.method == 'POST':
        # Recibir el ranking desde el formulario (lista ordenada de códigos)
        import json
        ranking_data = request.POST.get('ranking_data')

        if ranking_data:
            try:
                ranking_list = json.loads(ranking_data)

                # Generar código único para el ranking
                if existing_ranking:
                    # Actualizar existente
                    Ranking.objects.filter(
                        user=request.user.username,
                        category=category_code
                    ).update(rankingList=ranking_list)
                    messages.success(request, 'Ranking actualizado correctamente.')
                else:
                    # Crear nuevo
                    last_code = Ranking.objects.order_by('-code').values_list('code', flat=True).first()
                    next_code = (last_code or 0) + 1

                    Ranking.objects.create(
                        code=next_code,
                        user=request.user.username,
                        category=category_code,
                        rankingList=ranking_list
                    )
                    messages.success(request, 'Ranking creado correctamente.')

                return redirect('ranking_categoria_global', category_code=category_code)
            except Exception as e:
                messages.error(request, f'Error al guardar el ranking: {str(e)}')

    # Preparar datos del ranking existente
    ranked_games = []
    unranked_games = videojuegos.copy()

    if existing_ranking:
        ranking_list = existing_ranking.rankingList or []
        for game_code in ranking_list:
            game = next((g for g in videojuegos if g.code == game_code), None)
            if game:
                ranked_games.append(game)
                unranked_games.remove(game)

    # Preparar datos para el template
    import json
    context = {
        'categoria': categoria,
        'ranked_games': ranked_games,
        'unranked_games': unranked_games,
        'is_edit': existing_ranking is not None
    }
    return render(request, 'ranking_crear.html', context)


@login_required
def ranking_delete(request, category_code):
    if request.method == 'POST':
        try:
            Ranking.objects.filter(
                user=request.user.username,
                category=category_code
            ).delete()
            messages.success(request, 'Tier list eliminado correctamente.')
        except Exception:
            messages.error(request, 'Error al eliminar el tier list.')
    return redirect('ranking_categoria_global', category_code=category_code)


@login_required
def review_delete(request, game_code, serie):
    review = get_object_or_404(Review, code=game_code, serie=serie)

    # Verificar que el usuario sea el autor o admin
    if review.user != request.user.username and request.user.role != 'admin':
        messages.error(request, 'No tienes permiso para borrar esta reseña.')
        return redirect('game_detail', code=game_code)

    if request.method == 'POST':
        # Como Review es managed=False y no tiene PK explícita (id),
        # borramos filtrando directamente para evitar errores de atributo id=None
        Review.objects.filter(code=game_code, serie=serie).delete()
        messages.success(request, 'Reseña eliminada correctamente.')
        return redirect('game_detail', code=game_code)

    return render(request, 'review_confirm_delete.html', {
        'review': review,
        'game_code': game_code
    })


# Agregar estas vistas al final de tu archivo views.py

@staff_member_required
def user_list(request):
    """Listar todos los usuarios del sistema"""
    User = get_user_model()
    usuarios = User.objects.all().order_by('-id')
    return render(request, 'user_list.html', {'usuarios': usuarios})


@staff_member_required
def user_delete(request, user_id):
    """Eliminar un usuario"""
    if request.method == 'POST':
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        # Evitar que el admin se elimine a sí mismo
        if user.id == request.user.id:
            messages.error(request, 'No puedes eliminarte a ti mismo.')
            return redirect('user_list')

        try:
            username = user.username
            user.delete()
            messages.success(request, f'Usuario "{username}" eliminado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el usuario: {str(e)}')

    return redirect('user_list')


@staff_member_required
def user_toggle_staff(request, user_id):
    """Alternar el estado de staff de un usuario"""
    if request.method == 'POST':
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        # Evitar que el admin se quite sus propios permisos
        if user.id == request.user.id:
            messages.error(request, 'No puedes modificar tus propios permisos.')
            return redirect('user_list')

        try:
            user.is_staff = not user.is_staff
            user.save()
            status = "activado" if user.is_staff else "desactivado"
            messages.success(request, f'Permisos de staff {status} para "{user.username}".')
        except Exception as e:
            messages.error(request, f'Error al modificar el usuario: {str(e)}')

    return redirect('user_list')


@staff_member_required
def user_toggle_role(request, user_id):
    """Cambiar el rol del usuario entre admin y cliente"""
    if request.method == 'POST':
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        # Evitar que el admin cambie su propio rol
        if user.id == request.user.id:
            messages.error(request, 'No puedes cambiar tu propio rol.')
            return redirect('user_list')

        try:
            user.role = 'admin' if user.role == 'cliente' else 'cliente'
            user.save()
            messages.success(request, f'Rol de "{user.username}" cambiado a {user.role}.')
        except Exception as e:
            messages.error(request, f'Error al cambiar el rol: {str(e)}')

    return redirect('user_list')