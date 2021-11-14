from django.contrib.auth import validators
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        user = self.model(
            username=username,
            last_login=timezone.now(),
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


# custom auth_user_model
class User(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'user'

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'


class Shopper(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=30)
    age = models.IntegerField()
    
    class Meta:
        db_table = 'shopper'

    def __str__(self):
        return self.name


class Wholesaler(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'wholesaler'

    def __str__(self):
        return self.name
