from django.db.models import (
    Model, ForeignKey, ManyToManyField, DO_NOTHING, OneToOneField, 
    AutoField, CharField, ImageField,  BooleanField, BigAutoField, DateTimeField,
    IntegerField,
)
from django.utils import timezone

from common import storage


class MainCategory(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)
    image_url = ImageField(max_length=200, storage=storage.ClientSVGStorage)

    class Meta:
        db_table = 'main_category'
        ordering = ['id']

    def __str__(self):
        return self.name


class SubCategory(Model):
    id = AutoField(primary_key=True)
    main_category = ForeignKey('MainCategory', related_name='sub_categories', on_delete=DO_NOTHING)
    sizes = ManyToManyField('Size', through='SubCategorySize')
    name = CharField(max_length=20)
    require_product_additional_information = BooleanField()
    require_laundry_information = BooleanField()
    
    class Meta:
        db_table = 'sub_category'

    def __str__(self):
        return self.name


class Product(Model):
    id = BigAutoField(primary_key=True)
    wholesaler = ForeignKey('user.Wholesaler', DO_NOTHING)
    sub_category = ForeignKey('SubCategory', DO_NOTHING)
    style = ForeignKey('Style', DO_NOTHING)
    age = ForeignKey('Age', DO_NOTHING)
    tags = ManyToManyField('Tag', db_table='product_tag')
    laundry_informations = ManyToManyField('LaundryInformation', through='ProductLaundryInformation')
    name = CharField(max_length=60)
    code = CharField(max_length=12, default='AA')
    created = DateTimeField(default=timezone.now)
    price = IntegerField()
    on_sale = BooleanField(default=True)

    class Meta:
        db_table = 'product'

    def __str__(self):
        return self.name


class Age(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        db_table = 'age'
        ordering = ['id']


class Thickness(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        db_table = 'thickness'
        ordering = ['id']


class SeeThrough(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        db_table = 'see_through'
        ordering = ['id']


class Flexibility(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        db_table = 'flexibility'
        ordering = ['id']


class ProductAdditionalInformation(Model):
    product = OneToOneField('Product', DO_NOTHING, primary_key=True, related_name='product_additional_information')
    thickness = ForeignKey('Thickness', DO_NOTHING)
    see_through = ForeignKey('SeeThrough', DO_NOTHING)
    flexibility = ForeignKey('Flexibility', DO_NOTHING)
    lining = BooleanField()

    class Meta:
        db_table = 'product_additional_information'


class ProductImages(Model):
    id = BigAutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING, related_name='images')
    image_url = CharField(max_length=200)
    sequence = IntegerField()

    class Meta:
        db_table = 'product_images'
        ordering = ['sequence']
        unique_together = (('product', 'sequence'),)


class Tag(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'tag'

    def __str__(self):
        return self.name


class Color(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)
    image_url = ImageField(max_length=200, storage=storage.ClientSVGStorage)

    class Meta:
        db_table = 'color'
        ordering = ['id']

    def __str__(self):
        return self.name


class ProductColor(Model):
    id = AutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING, related_name='colors')
    color = ForeignKey('Color', DO_NOTHING)
    display_color_name = CharField(max_length=20)

    class Meta:
        db_table = 'product_color'
        unique_together = (('product', 'display_color_name'),)

    def save(self, *args, **kwargs):
        if not self.display_color_name:
            self.display_color_name = self.color.name
        super().save(*args, **kwargs)


class ProductColorImages(Model):
    id = AutoField(primary_key=True)
    product_color = ForeignKey('ProductColor', DO_NOTHING, related_name='images')
    image_url = CharField(max_length=200)
    sequence = IntegerField()

    class Meta:
        db_table = 'product_color_images'
        unique_together = (('product_color', 'sequence'), ('product_color', 'image_url'),)


class Size(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=10)

    class Meta:
        db_table = 'size'
        ordering = ['id']

    def __str__(self):
        return self.name


class SubCategorySize(Model):
    id = AutoField(primary_key=True)
    sub_category = ForeignKey('SubCategory', DO_NOTHING)
    size = ForeignKey('Size', DO_NOTHING)

    class Meta:
        db_table = 'sub_category_size'
        unique_together = (('sub_category', 'size'),)


class Option(Model):
    id = BigAutoField(primary_key=True)
    product_color = ForeignKey('ProductColor', DO_NOTHING, related_name='options')
    size = ForeignKey('Size', DO_NOTHING)
    display_size_name = CharField(max_length=20)
    price_difference = IntegerField(default=0)  

    class Meta:
        db_table = 'option'
        unique_together = (('product_color', 'size'),)

    def save(self, *args, **kwargs):
        if not self.display_size_name:
            self.display_size_name = self.size.name
        super().save(*args, **kwargs)


class Keyword(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'keyword'


class Style(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'style'
        ordering = ['id']


class LaundryInformation(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'laundry_information'
        ordering = ['id']


class ProductLaundryInformation(Model):
    id = BigAutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING)
    laundry_information = ForeignKey('LaundryInformation', DO_NOTHING)        

    class Meta:
        db_table = 'product_laundry_information'
        unique_together = (('product', 'laundry_information'),)


class Material(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'material'
        ordering = ['id']


class ProductMaterial(Model):
    id = AutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING, related_name='materials')
    material = CharField(max_length=20)
    mixing_rate = IntegerField()

    class Meta:
        db_table = 'product_material'
        unique_together = (('product', 'material'),)
