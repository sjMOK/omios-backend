from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.
class MemberManager(BaseUserManager):
    pass


class Member(AbstractBaseUser):
    objects = MemberManager()

    USERNAME_FIELD = 'id'
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    




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