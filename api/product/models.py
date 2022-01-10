from django.db.models import *
from django.utils import timezone

class Category(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'category'
        ordering = ['id']

    def __str__(self):
        return self.name


class SubCategory(Model):
    id = AutoField(primary_key=True)
    category = ForeignKey('Category', DO_NOTHING)
    name = CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'subcategory'

    def __str__(self):
        return self.name


class Product(Model):
    id = BigAutoField(primary_key=True)
    name = CharField(max_length=60)
    code = CharField(max_length=12)
    subcategory = ForeignKey('SubCategory', DO_NOTHING)
    created = DateTimeField(default=timezone.now)
    price = IntegerField()
    wholesaler = ForeignKey('user.Wholesaler', DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product'

    def __str__(self):
        return self.name


class Color(Model):
    name = CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'color'

    def __str__(self):
        return self.name


class Size(Model):
    name = CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'size'

    def __str__(self):
        return self.name


class Option(Model):
    id = BigAutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING)
    color = ForeignKey('Color', DO_NOTHING)
    display_color_name = CharField(max_length=10)
    price = IntegerField()
    sequence = IntegerField()
    size = ForeignKey('Size', DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'option'
