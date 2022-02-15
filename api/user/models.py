import string, random
from django.db.models import *
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


class Membership(Model):
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'membership'

    def __str__(self):
        return self.name


class User(AbstractBaseUser):
    id = BigAutoField(primary_key=True)
    username = CharField(max_length=20, unique=True)
    is_admin = BooleanField(default=False)
    is_active = BooleanField(default=True)
    last_update_password = DateTimeField()
    created_at = DateTimeField(default=timezone.now)
    deleted_at = DateTimeField(null=True)
    
    class Meta:
        db_table = 'user'

    objects = BaseUserManager()

    USERNAME_FIELD = 'username'

    def __set_password(self, update_time):
        super().set_password(self.password)
        self.last_update_password = update_time

    def save(self, force_insert=False, update_fields=None, *args, **kwargs):
        if self._password is not None:
            raise APIException('The save method cannot be used when the public set_password method is used.')
        elif (not force_insert and update_fields is None):
            raise APIException('User model save method requires force_insert or update_fields.')

        if force_insert:
            self.__set_password(self.created_at)
        elif update_fields and 'password' in update_fields:
            self.__set_password(timezone.now())

        super().save(force_insert=force_insert, update_fields=update_fields, *args, **kwargs)


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
        db_table = 'shopper'

    def __str__(self):
        return '{0} {1}'.format(self.username, self.name)

    def __get_default_nickname(self):
        self.nickname = self.username
        while self.__class__.objects.filter(nickname=self.nickname).exists():
            length = random.randint(5, 14)
            self.nickname = 'omios_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

        return self.nickname

    def save(self, *args, **kwargs):
        if not self.nickname:
            self.nickname = self.__get_default_nickname()

        super().save(*args, **kwargs)


class Wholesaler(User):
    user = OneToOneField(User, DO_NOTHING, parent_link=True, primary_key=True)
    name = CharField(max_length=60)
    email = EmailField(max_length=50)
    phone = CharField(max_length=15)
    company_registration_number = CharField(max_length=12, unique=True)

    class Meta:
        db_table = 'wholesaler'

    def __str__(self):
        return '{0} {1}'.format(self.username, self.name)
