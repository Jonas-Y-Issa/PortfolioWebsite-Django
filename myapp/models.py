from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models


project_url_validator = URLValidator(schemes=["http", "https"])


class About(models.Model):
    description = models.TextField()
    image = models.ImageField()
    image_desc = models.CharField(max_length=100)


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


class Skills(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()


class Apps(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
