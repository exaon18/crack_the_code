from django.db import models
from django.contrib.auth import get_user_model

MyUser = get_user_model()

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0, null=False)
    phone_number = models.CharField(max_length=20, null=False)
    ResponseTime = models.DateTimeField(auto_now_add=True, null=False)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='pending')
    requestedAt=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"
class DepositRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0, null=False)
    tx_id = models.CharField(max_length=20, null=False)
    ResponseTime = models.DateTimeField(auto_now_add=True, null=False)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='pending')
    requestedAt=models.DateTimeField(auto_now_add=True)
    SenderName=models.CharField(max_length=200,null=True)
    def __str__(self):
        return f"{self.user.username} - {self.status}"
class TelebirrReq(models.Model):
    Name=models.CharField(null=True,max_length=20)
    tx_id=models.CharField(null=False,max_length=10)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    
    completed=models.BooleanField(default=False)
    def __str__(self):
        return f"{self.Name} - {self.tx_id}"
