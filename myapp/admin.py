from django.contrib import admin

from .models import About, Apps, Project, Skills

admin.site.register(Project)
admin.site.register(Skills)
admin.site.register(About)
admin.site.register(Apps)
