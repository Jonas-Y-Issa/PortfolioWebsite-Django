from django.urls import path
from .views import index, favicon

urlpatterns = [
    path('', index, name='index'),
    path("favicon.ico", favicon),
]