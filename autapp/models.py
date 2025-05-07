from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class MyUser(AbstractUser):
    token = models.CharField(max_length=200,null=True)
    groups = models.ManyToManyField(Group, related_name='myuser_set')
    user_permissions = models.ManyToManyField(Permission, related_name='myuser_permissions_set')
    is_logged_in=models.BooleanField(default=False)
    withdrawalToken=models.IntegerField(null=True)
    pendingWithdrwal=models.BooleanField(default=False)
    pendingDeposit=models.BooleanField(default=False)
    points=models.IntegerField(default=0)
    forgetPasswordToken=models.IntegerField(null=True)
    last_otp_sent = models.DateTimeField(null=True, blank=True)
    Active_Game=models.BooleanField(default=False)
    def __str__(self):
        return self.username
class Ballance(models.Model):
    user= models.OneToOneField(MyUser, on_delete=models.CASCADE, null=False)
    ballance=models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    def __str__(self):
        return self.user.username
  
    
class GameHistory(models.Model):
    user= models.OneToOneField(MyUser,on_delete=models.CASCADE, null=False)
    TotalPlayed=models.IntegerField(default=0)
    TotalWin=models.IntegerField(default=0)
    Totaloss=models.IntegerField(default=0)
    TotalEarning=models.DecimalField(max_digits=100,decimal_places=3, default=0.00)

    def __str__(self):
        return self.user.username
class InGame(models.Model):
    user= models.ForeignKey(MyUser, on_delete=models.CASCADE, null=False)
     
    Bet_amount=models.DecimalField(max_digits=100,decimal_places=3, default=0.00)
    GameType=models.CharField(max_length=10)
    Win=models.BooleanField(default=False)
    DateOfGame=models.DateField(auto_now_add=True, null=True)
    def __str__(self):
        return self.user.username


