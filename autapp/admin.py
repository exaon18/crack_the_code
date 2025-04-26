from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser,Ballance,GameHistory,InGame
from monitary.models import TelebirrReq

admin.site.register(MyUser, UserAdmin,)

admin.site.register(InGame)
admin.site.register(Ballance)
admin.site.register(GameHistory)
admin.site.register(TelebirrReq)