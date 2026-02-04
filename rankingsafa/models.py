import datetime
from django.utils import timezone

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Create your models here.


class Videojuego(models.Model):
    code = models.IntegerField(null=False)
    name = models.CharField(max_length=300)
    desc = models.TextField()
    category = ArrayField(models.IntegerField(), null=True,blank=True, default=list)
    image = models.URLField(max_length=500, null=True, blank=True)
    developer = models.CharField(max_length=300, null=True, blank=True)
    publisher = models.CharField(max_length=300, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    platforms = ArrayField(models.CharField(max_length=100), null=True, blank=True, default=list)
    price = models.FloatField(null=True, blank=True)
    age_rating = models.CharField(max_length=10, null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    multiplayer = models.BooleanField(default=False)

    class Meta:
        db_table = 'videojuegos'
        managed = False

    def __str__(self):
        return self.name


class Categoria(models.Model):
    code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=300, unique=True)
    desc = models.TextField()
    image = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'categorias'
        managed = False

class Review(models.Model):
    code = models.IntegerField(null=False)
    serie = models.IntegerField(null=False)
    user = models.CharField(max_length=300)
    reviewDate = models.DateField(default=timezone.now)
    rating = models.IntegerField(default=0, validators=[MaxValueValidator(5), MinValueValidator(0)])
    comentary = models.TextField()

    class Meta:
        db_table = 'reviews'
        managed = False

    def __str__(self):
        return self.user + " " + str(self.rating)

class Ranking(models.Model):
    code = models.IntegerField(null=False)
    user = models.CharField(max_length=300)
    rankDate = models.DateField(default=timezone.now)
    category = models.IntegerField(null=False)
    rankingList = ArrayField(models.IntegerField(), null=True,blank=True, default=list)

    class Meta:
        db_table = 'rankings'
        managed = False

    def __str__(self):
        return self.user + " " + str(self.rankDate)

class UserManager(BaseUserManager):
    def create_user(self, mail, username, role, password=None):
        if not mail or not username or not role:
            raise ValueError("Debes rellenar los campos requeridos (mail, username, role)")
        mail = self.normalize_email(mail)
        user = self.model(mail=mail, username=username, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mail, username, role='admin', password=None):
        user = self.create_user(mail, username, role, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user



class User(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    )

    mail = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='cliente')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['mail',  'role']

    def __str__(self):
        return self.username
