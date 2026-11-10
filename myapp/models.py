from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models


project_url_validator = URLValidator(schemes=["http", "https"])


class About(models.Model):
    description = models.TextField()
    image = models.ImageField(blank=True)
    image_desc = models.CharField(max_length=100, blank=True)


class Project(models.Model):
    inc = models.IntegerField()
    preface = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    extLink = models.URLField(validators=[project_url_validator])
    description = models.TextField()
    image = models.ImageField()

    @property
    def public_url(self):
        """Validate stored URLs too: imports and ORM saves bypass form validation."""
        try:
            project_url_validator(self.extLink)
        except ValidationError:
            return ""
        return self.extLink


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name="gallery", on_delete=models.CASCADE)
    image = models.CharField(
        max_length=200,
        help_text="Image filename relative to homepage/images/.",
    )
    caption = models.CharField(max_length=150)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return f"{self.project.title}: {self.caption}"


class Skills(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()


class Apps(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
