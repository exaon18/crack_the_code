from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', views.login_view, name='login'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('activate/<str:user>', views.activate, name='activate'),
    path('join_game', views.join_game, name='join_game'),
]
from django.conf.urls import handler404
from django.shortcuts import render

def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = 'autapp.urls.custom_404'
