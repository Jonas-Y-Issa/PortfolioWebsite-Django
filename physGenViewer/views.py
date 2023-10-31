from django.shortcuts import render
from MyWebsite.settings import STATIC_URL 
import os
from pathlib import Path
from myapp.views import base
# Create your views here.
STAT_DIR = Path(__file__).resolve().parent.parent


def physics(request):
    path=(STAT_DIR / "staticfiles/physics")
    css_list = os.listdir(path / "css")   
    scripts_list = os.listdir(path / "scripts")   
    return render(request, 'physics.html', 
        {'styles': css_list,
        'js_script': scripts_list,
         'stat': STATIC_URL,
         'base': base()})

