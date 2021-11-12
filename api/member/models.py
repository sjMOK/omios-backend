from django.contrib.auth import validators
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class CustomMemberManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        # if not username:
        #     raise ValueError("Members must have an username")
        
        member = self.model(
            username=username,
            last_login=timezone.now(),
            **extra_fields
        )

        member.set_password(password)
        member.save(using=self._db)
        return member

    def create_superuser(self, username, password=None):
        member = self.create_user(
            username,
            password=password,
        )
        member.is_admin = True
        member.save(using=self._db)
        return member


# custom auth_user_model
class Member(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'member'

    objects = CustomMemberManager()

    USERNAME_FIELD = 'username'


class Shopper(models.Model):
    member = models.OneToOneField('Member', on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=30)
    age = models.IntegerField()
    
    class Meta:
        db_table = 'shopper'

    def __str__(self):
        return self.name


class Wholesaler(models.Model):
    member = models.OneToOneField('Member', on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'wholesaler'

    def __str__(self):
        return self.name
