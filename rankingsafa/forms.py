from django import forms
from django.contrib.auth.forms import AuthenticationForm
from rankingsafa.models import *


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Contraseña'}))
    repeat_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Repetir contraseña'}),
        label="Repetir Contraseña")

    class Meta:
        model = User
        fields = ('username', 'mail', 'password')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nombre de usuario'}),
            'mail': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'Correo electrónico'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        repeat_password = cleaned_data.get("repeat_password")

        if password != repeat_password:
            raise forms.ValidationError(
                "Las contraseñas no coinciden."
            )
        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nombre de usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Contraseña'}))


class UploadJSONForm(forms.Form):
    json_file = forms.FileField(
        label="Selecciona un archivo JSON",
        widget=forms.FileInput(attrs={'class': 'file-input'})
    )


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['name', 'desc', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nombre de la categoría'}),
            'desc': forms.Textarea(attrs={'class': 'textarea', 'placeholder': 'Descripción de la categoría'}),
            'image': forms.URLInput(attrs={'class': 'input', 'placeholder': 'URL de la imagen o icono'}),
        }


class VideojuegoForm(forms.ModelForm):
    # Campo oculto para las categorías (se manejará con JavaScript)
    category = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'category-input'}),
        label='Categorías'
    )

    platforms = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea',
            'placeholder': 'PC, PlayStation 5, Xbox Series X, Nintendo Switch',
            'rows': 2
        }),
        label='Plataformas',
        help_text='Separadas por comas'
    )

    class Meta:
        model = Videojuego
        fields = ['name', 'desc', 'image', 'developer', 'publisher',
                  'release_date', 'category', 'platforms', 'price',
                  'age_rating', 'duration', 'multiplayer']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nombre del juego'}),
            'desc': forms.Textarea(attrs={'class': 'textarea', 'placeholder': 'Descripción del juego', 'rows': 4}),
            'image': forms.URLInput(attrs={'class': 'input', 'placeholder': 'URL de la imagen'}),
            'developer': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Desarrollador'}),
            'publisher': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Publisher/Editorial'}),
            'release_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'age_rating': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: PEGI 16, E10+'}),
            'duration': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'placeholder': 'Horas'}),
            'multiplayer': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }

    def clean_category(self):
        """Convert JSON string to list of integers for ArrayField"""
        import json
        category_data = self.cleaned_data.get('category', '')

        # Si está vacío, devolver lista vacía
        if not category_data or not category_data.strip():
            return []

        try:
            # Parsear el JSON string a lista de Python
            parsed = json.loads(category_data)
            # Asegurarse de que es una lista y convertir a enteros
            if isinstance(parsed, list):
                return [int(x) for x in parsed if x is not None]
            return []
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # Si hay error, devolver lista vacía
            return []

    def clean_platforms(self):
        """Convert comma-separated string to list"""
        platforms_data = self.cleaned_data.get('platforms')
        if platforms_data:
            # Dividir por comas y limpiar espacios
            return [p.strip() for p in platforms_data.split(',') if p.strip()]
        return []


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comentary']
        labels = {
            'rating': 'Puntuación (0-5)',
            'comentary': 'Comentario',
        }
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'input', 'min': 0, 'max': 5}),
            'comentary': forms.Textarea(
                attrs={'class': 'textarea', 'placeholder': 'Escribe tu opinión aquí...', 'rows': 4}),
        }