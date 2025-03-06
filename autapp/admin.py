from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser,Ballance,GameHistory,InGame

admin.site.register(MyUser, UserAdmin,)

admin.site.register(InGame)
admin.site.register(Ballance)
admin.site.register(GameHistory)