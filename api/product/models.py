from django.db.models import *
from django.utils import timezone

from common import storage

class MainCategory(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)
    image_url = ImageField(max_length=200, storage=storage.ClientSVGStorage)

    class Meta:
        managed = False
        db_table = 'main_category'
        ordering = ['id']

    def __str__(self):
        return self.name


class SubCategory(Model):
    id = AutoField(primary_key=True)
    main_category = ForeignKey('MainCategory', DO_NOTHING)
    name = CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'sub_category'

    def __str__(self):
        return self.name


class Product(Model):
    id = BigAutoField(primary_key=True)
    name = CharField(max_length=60)
    code = CharField(max_length=12, default='AA')
    sub_category = ForeignKey('SubCategory', DO_NOTHING)
    created = DateTimeField(default=timezone.now)
    price = IntegerField()
    wholesaler = ForeignKey('user.Wholesaler', DO_NOTHING)
    on_sale = IntegerField(default=True)

    class Meta:
        managed = False
        db_table = 'product'

    def __str__(self):
        return self.name


class ProductImages(Model):
    id = BigAutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING, related_name='images')
    url = ImageField(max_length=200, upload_to=storage.product_image_path)

    class Meta:
        managed = False
        db_table = 'product_images'


class Color(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)
    image_url = ImageField(max_length=200, storage=storage.ClientSVGStorage)

    class Meta:
        managed = False
        db_table = 'color'

    def __str__(self):
        return self.name


class Size(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=10)

    class Meta:
        managed = False
        db_table = 'size'
        ordering = ['id']

    def __str__(self):
        return self.name


class Option(Model):
    id = BigAutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING, related_name='options')
    size = ForeignKey('Size', DO_NOTHING)
    color = ForeignKey('Color', DO_NOTHING)
    display_color_name = CharField(max_length=20)
    price_difference = IntegerField()

    class Meta:
        managed = False
        db_table = 'option'
