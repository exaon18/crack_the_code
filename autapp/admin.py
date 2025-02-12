from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser,game,Ballance

admin.site.register(MyUser, UserAdmin)

admin.site.register(game)
admin.site.register(Ballance)