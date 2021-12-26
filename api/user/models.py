from django.contrib.auth import validators
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

class UserManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        user = self.model(
            username=username,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        user = self.create_user(
            username,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class Membership(models.Model):
    name = models.CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'membership'


class User(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=20, unique=True)
    is_admin = models.BooleanField(default=False)
    email = models.EmailField(max_length=50)
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    last_update_password = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user'

    objects = UserManager()

    USERNAME_FIELD = 'username'


class Shopper(models.Model):
    name = models.CharField(max_length=20)
    nickname = models.CharField(max_length=20, unique=True)
    gender = models.BooleanField()
    birthday = models.DateField()
    height = models.IntegerField(null=True)
    weight = models.IntegerField(null=True)
    membership = models.ForeignKey(Membership, models.DO_NOTHING)
    user = models.OneToOneField('User', models.CASCADE, primary_key=True)

    class Meta:
        managed = False
        db_table = 'shopper'

    def __str__(self):
        return self.name


class Wholesaler(models.Model):
    user = models.OneToOneField(User, models.CASCADE, primary_key=True)
    name = models.CharField(max_length=60)

    class Meta:
        managed = False
        db_table = 'wholesaler'

    def __str__(self):
        return self.name
