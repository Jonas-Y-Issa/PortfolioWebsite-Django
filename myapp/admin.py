from django.contrib import admin

from .models import About, Apps, Project, ProjectImage, Skills


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    fields = ("image", "caption", "position")
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectImageInline]


admin.site.register(Skills)
admin.site.register(About)
admin.site.register(Apps)
