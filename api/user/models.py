from django.db.models import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


class Membership(Model):
    name = CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'membership'

    def __str__(self):
        return self.name


class User(AbstractBaseUser):
    id = BigAutoField(primary_key=True)
    username = CharField(max_length=20, unique=True)
    is_admin = BooleanField(default=False)
    is_active = BooleanField(default=True)
    last_update_password = DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'user'

    objects = BaseUserManager()

    USERNAME_FIELD = 'username'


class Shopper(User):
    user = OneToOneField(User, DO_NOTHING, parent_link=True, primary_key=True)
    name = CharField(max_length=20)
    email = EmailField(max_length=50)
    phone = CharField(max_length=15, unique=True)
    nickname = CharField(max_length=20, unique=True)
    gender = BooleanField()
    birthday = DateField()
    height = IntegerField(null=True)
    weight = IntegerField(null=True)
    membership = ForeignKey(Membership, DO_NOTHING, default=1)

    class Meta:
        managed = False
        db_table = 'shopper'

    def __str__(self):
        return '{0} {1}'.format(self.username, self.name)


class Wholesaler(User):
    user = OneToOneField(User, DO_NOTHING, parent_link=True, primary_key=True)
    name = CharField(max_length=60)
    email = EmailField(max_length=50)
    phone = CharField(max_length=15)
    company_registration_number = CharField(max_length=12, unique=True)

    class Meta:
        managed = False
        db_table = 'wholesaler'

    def __str__(self):
        return '{0} {1}'.format(self.username, self.name)
