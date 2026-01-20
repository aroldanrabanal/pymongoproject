import datetime
from datetime import timezone

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_mongodb_backend.models import EmbeddedModel


# Create your models here.


class Videojuego(EmbeddedModel):
    code = models.IntegerField(null=False)
    name = models.CharField(max_length=300)
    desc = models.TextField()
    category = ArrayField(models.IntegerField(), null=True,blank=True, default=list)
    image = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'videojuegos'
        managed = False

    def __str__(self):
        return self.name


class Categoria(EmbeddedModel):
    code = models.IntegerField(null=False)
    name = models.CharField(max_length=300, unique=True)
    desc = models.TextField()

    class Meta:
        db_table = 'categorias'
        managed = False

class Review(EmbeddedModel):
    code = models.IntegerField(null=False)
    serie = models.IntegerField(null=False)
    user = models.CharField(max_length=300)
    reviewDate = models.DateField(default=datetime.datetime.now())
    rating = models.IntegerField(default=0, validators=[MaxValueValidator(5), MinValueValidator(0)])
    comentary = models.TextField()

    class Meta:
        db_table = 'reviews'
        managed = False

    def __str__(self):
        return self.user + " " + str(self.rating)

class Ranking(EmbeddedModel):
    code = models.IntegerField(null=False)
    user = models.CharField(max_length=300)
    rankDate = models.DateField(default=datetime.datetime.now())
    category = models.IntegerField(null=False)
    rankingList = ArrayField(models.IntegerField(), null=True,blank=True, default=list)

    class Meta:
        db_table = 'rankings'
        managed = False

    def __str__(self):
        return self.user + " " + str(self.rankDate)