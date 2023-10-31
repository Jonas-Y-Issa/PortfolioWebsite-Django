import os
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from MyWebsite.settings import STATIC_URL 
from pathlib import Path
from myapp.models import Project, Skills, About, Apps

STAT_DIR = Path(__file__).resolve().parent.parent


def base():
    basepath=(STAT_DIR / "staticfiles/base")
    base_css_list = os.listdir(basepath / "css")   
    base_scripts_list = os.listdir(basepath / "scripts")   
    base_images_list = os.listdir(basepath / "images")   
    base_fonts_list = os.listdir(basepath / "fonts")

    base_array = {  'styles': base_css_list,
                    'js_script': base_scripts_list,
                    'images': base_images_list,
                    'stat': STATIC_URL,
                    'font': base_fonts_list}
    return(base_array)

def index(request):
    path=(STAT_DIR / "staticfiles/homepage")
    css_list = os.listdir(path / "css")   
    scripts_list = os.listdir(path / "scripts")   
    images_list = os.listdir(path / "images")   
    app_list = Apps.objects.all()
    project_db = Project.objects.all()
    skill_list = Skills.objects.all()
    about_list = About.objects.all()
    return render(request, 'Index.html',
     {'styles': css_list,
      'js_script': scripts_list,
       'images': images_list,
         'stat': STATIC_URL,
         'apps':app_list,
         'projects':project_db,
         'skills': skill_list,
         'about':about_list,
         'base': base()})

@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # one day
def favicon(request: HttpRequest) -> HttpResponse:
    file = (settings.BASE_DIR / "myapp/static/base/images" / "favicon.svg").open("rb")
    return FileResponse(file)



