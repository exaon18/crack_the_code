from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import MyUser,Game

admin.site.register(MyUser, UserAdmin)
admin.site.register(Game)
