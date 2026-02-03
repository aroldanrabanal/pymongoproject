from django import forms
from django.contrib.auth.forms import AuthenticationForm
from rankingsafa.models import *


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Contraseña'}))
    repeat_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Repetir contraseña'}), label="Repetir Contraseña")

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

