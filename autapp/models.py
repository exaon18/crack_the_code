from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class MyUser(AbstractUser):
    token = models.CharField(max_length=200,null=True)
    groups = models.ManyToManyField(Group, related_name='myuser_set')
    user_permissions = models.ManyToManyField(Permission, related_name='myuser_permissions_set')
    
    
    def __str__(self):
        return self.username
class Ballance(models.Model):
    user= models.OneToOneField(MyUser, on_delete=models.CASCADE, null=False)
    ballance=models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    def __str__(self):
        return self.user.username
  # Ensure you have the correct user model
class game(models.Model):
    user= models.OneToOneField(MyUser, on_delete=models.CASCADE, null=False)
    Total_Game=models.IntegerField(default=0)
    Win_Game=models.IntegerField(default=0)
    Lose_Game=models.IntegerField(default=0)
    TotalWinings=models.IntegerField(default=0)
    def __str__(self):
        return self.user.username
    

