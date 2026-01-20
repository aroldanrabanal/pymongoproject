from django.shortcuts import render
# Create your views here.
def mostrar_inicio(request):
    return render(request, 'inicio.html')