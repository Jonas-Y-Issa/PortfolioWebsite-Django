from django.db import models


# Create your models here.
class Project(models.Model):
    inc = models.IntegerField();
    preface = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    extLink = models.URLField();
    description = models.TextField()
    image = models.ImageField();



class Skills(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()

