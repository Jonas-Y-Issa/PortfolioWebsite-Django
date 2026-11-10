import re

from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from .models import About, Project, Skills


def index(request: HttpRequest) -> HttpResponse:
    skills = [
        {
            "title": skill.title.rstrip(":"),
            "items": [
                item.strip()
                for item in re.split(r"[|\r\n]+", skill.description)
                if item.strip()
            ],
        }
        for skill in Skills.objects.order_by("pk")
    ]
    return render(
        request,
        "Index.html",
        {
            "projects": Project.objects.order_by("inc", "pk").prefetch_related("gallery"),
            "skills": skills,
            "about": About.objects.order_by("pk"),
        },
    )


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # one day
def favicon(request: HttpRequest) -> HttpResponse:
    favicon_path = settings.BASE_DIR / "myapp/static/base/images/favicon.svg"
    return FileResponse(favicon_path.open("rb"))
