import os
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from MyWebsite.settings import STATIC_URL 
from pathlib import Path
from myapp.models import Project, Skills, About

STAT_DIR = Path(__file__).resolve().parent.parent

def index(request):
    path=(STAT_DIR / "staticfiles")
    css_list = os.listdir(path / "css")   
    scripts_list = os.listdir(path / "scripts")   
    images_list = os.listdir(path / "images")   
    fonts_list = os.listdir(path / "fonts")
    project_db = Project.objects.all()
    skill_list = Skills.objects.all()
    about_list = About.objects.all()
    return render(request, 'Index.html',
     {'styles': css_list,
      'js_script': scripts_list,
       'images': images_list,
        'fonts': fonts_list,
         'stat': STATIC_URL,
         'projects':project_db,
         'skills': skill_list,
         'about':about_list})

@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # one day
def favicon(request: HttpRequest) -> HttpResponse:
    file = (settings.BASE_DIR / "myapp/static/images" / "favicon.svg").open("rb")
    return FileResponse(file)



