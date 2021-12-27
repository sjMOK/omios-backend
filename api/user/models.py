from django.db.models import *
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


class Membership(Model):
    name = CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'membership'


class User(AbstractBaseUser):
    id = BigAutoField(primary_key=True)
    username = CharField(max_length=20, unique=True)
    is_admin = BooleanField(default=False)
    email = EmailField(max_length=50)
    phone = CharField(max_length=15)
    is_active = BooleanField(default=True)
    last_update_password = DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user'

    objects = UserManager()

    USERNAME_FIELD = 'username'


class Shopper(Model):
    name = CharField(max_length=20)
    nickname = CharField(max_length=20, unique=True)
    gender = BooleanField()
    birthday = DateField()
    height = IntegerField(null=True)
    weight = IntegerField(null=True)
    membership = ForeignKey(Membership, DO_NOTHING, default=1)
    user = OneToOneField('User', CASCADE, primary_key=True)

    class Meta:
        managed = False
        db_table = 'shopper'

    def __str__(self):
        return self.name


class Wholesaler(Model):
    user = OneToOneField(User, CASCADE, primary_key=True)
    name = CharField(max_length=60)

    class Meta:
        managed = False
        db_table = 'wholesaler'

    def __str__(self):
        return self.name
