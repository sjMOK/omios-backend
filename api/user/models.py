import string, random

from django.db.models import (
    Model, AutoField, BigAutoField, CharField, BooleanField, DateTimeField, OneToOneField, 
    ForeignKey, EmailField, DateField, IntegerField, ImageField, DO_NOTHING, ManyToManyField
)
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

from rest_framework.exceptions import APIException
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from common.storage import MediaStorage


class Membership(Model):
    id = AutoField(primary_key=True)
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
        elif update_fields:
            if 'password' in update_fields:
                self.__set_password(timezone.now())
                update_fields.append('last_update_password')
            if 'is_active' in update_fields:
                self.deleted_at = timezone.now()
                update_fields.append('deleted_at')

        super().save(force_insert=force_insert, update_fields=update_fields, *args, **kwargs)


class Shopper(User):
    user = OneToOneField(User, DO_NOTHING, parent_link=True, primary_key=True)
    membership = ForeignKey(Membership, DO_NOTHING, default=1)
    name = CharField(max_length=20)
    nickname = CharField(max_length=20, unique=True)
    mobile_number = CharField(max_length=11, unique=True)
    email = EmailField(max_length=50)
    gender = BooleanField()
    birthday = DateField()
    height = IntegerField(null=True)
    weight = IntegerField(null=True)

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


class ShopperShippingAddress(Model):
    id = BigAutoField(primary_key=True)
    shopper = ForeignKey('Shopper', DO_NOTHING)
    name = CharField(max_length=20, null=True)
    receiver_name = CharField(max_length=20)
    mobile_number = CharField(max_length=11)
    phone_number = CharField(max_length=11, null=True)
    zip_code = CharField(max_length=5)
    base_address = CharField(max_length=200)
    detail_address = CharField(max_length=100)
    is_default = BooleanField()

    class Meta:
        db_table = 'shopper_shipping_address'


class Wholesaler(User):
    user = OneToOneField(User, DO_NOTHING, parent_link=True, primary_key=True)
    name = CharField(max_length=60)
    mobile_number = CharField(max_length=11)
    phone_number = CharField(max_length=11, unique=True)
    email = EmailField(max_length=50)
    company_registration_number = CharField(max_length=12, unique=True)
    business_registration_image_url = ImageField(max_length=200, storage=MediaStorage)
    zip_code = CharField(max_length=5)
    base_address = CharField(max_length=200)
    detail_address = CharField(max_length=100)
    is_approved = BooleanField(default=False)

    class Meta:
        db_table = 'wholesaler'

    def __str__(self):
        return '{0} {1}'.format(self.username, self.name)


class Floor(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=10)

    class Meta:
        db_table = 'floor'
        ordering = ['id']

    def __str__(self):
        return self.name


class Building(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)
    zip_code = CharField(max_length=5)
    base_address = CharField(max_length=200)
    floors = ManyToManyField('Floor', through='BuildingFloor')

    class Meta:
        db_table = 'building'


class BuildingFloor(Model):
    id = AutoField(primary_key=True)
    building = ForeignKey('Building', DO_NOTHING)
    floor = ForeignKey('Floor', DO_NOTHING)

    class Meta:
        db_table = 'building_floor'
        unique_together = (('building', 'floor'),)
