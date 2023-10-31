from django.urls import path
from . import views

urlpatterns = [
    #path('book/<int:book_id>', views.physics),
    path('', views.physics, name='physics_gen'),

]