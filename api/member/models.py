from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Shopper(models.Model):
    login_id = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    email = models.CharField(max_length=100)
    gender = models.IntegerField()
    birthday = models.DateField()

    class Meta:
        managed = False
        db_table = 'shopper'