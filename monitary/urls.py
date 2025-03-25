from django.urls import path
from . import views
urlpatterns=[
    path("chiweA/<str:username>",views.ChiweA, name="chiweA"),
    path("deposit/", views.deposit,name='deposit'),
    path('withdraw/',views.withdraw,name="withdraw"),
    path("Monitering/<str:admin>", views.Monitering, name="Monitering")

]