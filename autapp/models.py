from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class MyUser(AbstractUser):
    token = models.CharField(max_length=200,null=True)
    groups = models.ManyToManyField(Group, related_name='myuser_set')
    user_permissions = models.ManyToManyField(Permission, related_name='myuser_permissions_set')
    ballance=models.IntegerField(default=0)

    def __str__(self):
        return self.username
  # Ensure you have the correct user model


