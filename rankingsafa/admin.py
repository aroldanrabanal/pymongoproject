from django.contrib import admin
from .models import Videojuego, Categoria, Review, Ranking, User

# Register your models here.
admin.site.register(Videojuego)
admin.site.register(Categoria)
admin.site.register(Review)
admin.site.register(Ranking)
admin.site.register(User)
