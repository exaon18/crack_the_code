from django.urls import path
from . import views

urlpatterns = [
    
    path('<str:game_type>', views.game, name='game'),
]