from django.shortcuts import render
from django.http import HttpResponse
import os

from MyWebsite.settings import STATIC_URL 
from .models import Book
# Create your views here.

def index(request):
    path=(settings.BASE_DIR / "myapp/static")
    css_list = os.listdir(path / "css")   
    scripts_list = os.listdir(path / "scripts")   
    images_list = os.listdir(path / "images")   
    fonts_list = os.listdir(path / "fonts")
    return render(request, 'Index.html',
     {'styles': css_list,
      'js_script': scripts_list,
       'images': images_list,
        'fonts': fonts_list,
         'stat': STATIC_URL})


from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # one day
def favicon(request: HttpRequest) -> HttpResponse:
    file = (settings.BASE_DIR / "myapp/static/images" / "favicon.svg").open("rb")
    return FileResponse(file)



