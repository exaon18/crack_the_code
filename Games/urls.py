from django.urls import path
from . import views
urlpatterns=[
    path('ctc/', views.ctc, name='ctc'),
    path("bingo/", views.bingo, name="bingo"),
    
]