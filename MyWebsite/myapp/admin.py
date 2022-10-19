from django.contrib import admin

# Register your models here.
from .models import Project, Skills

admin.site.register(Project)
admin.site.register(Skills)

