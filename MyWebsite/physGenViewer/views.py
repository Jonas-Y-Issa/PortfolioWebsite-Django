from django.shortcuts import render
from MyWebsite.settings import STATIC_URL 
import os
from pathlib import Path

# Create your views here.
STAT_DIR = Path(__file__).resolve().parent.parent


def physics(request):
    path=(STAT_DIR / "staticfiles")
    css_list = os.listdir(path / "css")   
    scripts_list = os.listdir(path / "scripts")   
    images_list = os.listdir(path / "images")   
    fonts_list = os.listdir(path / "fonts")
    return render(request, 'physics.html', {'styles': css_list,
      'js_script': scripts_list,
       'images': images_list,
        'fonts': fonts_list,
         'stat': STATIC_URL})