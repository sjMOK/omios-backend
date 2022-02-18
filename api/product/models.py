from django.db.models import *
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
    name = CharField(max_length=20)
    sizes = ManyToManyField('Size', through='SubCategorySize')

    class Meta:
        db_table = 'sub_category'

    def __str__(self):
        return self.name


class SubCategorySize(Model):
    id = AutoField(primary_key=True)
    sub_category = ForeignKey('SubCategory', DO_NOTHING)
    size = ForeignKey('Size', DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'sub_category_size'
        unique_together = (('sub_category', 'size'),)


class Product(Model):
    id = BigAutoField(primary_key=True)
    name = CharField(max_length=60)
    code = CharField(max_length=12, default='AA')
    sub_category = ForeignKey('SubCategory', DO_NOTHING)
    created = DateTimeField(default=timezone.now)
    price = IntegerField()
    wholesaler = ForeignKey('user.Wholesaler', DO_NOTHING)
    on_sale = BooleanField(default=True)
    style = ForeignKey('Style', DO_NOTHING)
    tags = ManyToManyField('Tag', through='ProductTag')
    laundry_informations = ManyToManyField('LaundryInformation', through='ProductLaundryInformation')
    age = ForeignKey('Age', DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product'

    def __str__(self):
        return self.name


class Age(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'age'


class Thickness(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'thickness'


class SeeThrough(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'see_through'


class Flexibility(Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'flexibility'


class ProductAdditionalInformation(Model):
    product = OneToOneField('Product', DO_NOTHING, primary_key=True)       
    thickness = ForeignKey('Thickness', DO_NOTHING)
    see_through = ForeignKey('SeeThrough', DO_NOTHING)
    flexibility = ForeignKey('Flexibility', DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_additional_information'


class ProductImages(Model):
    id = BigAutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING, related_name='images')
    url = CharField(max_length=200)
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


class ProductTag(Model):
    id = AutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING)
    tag = ForeignKey('Tag', DO_NOTHING)

    class Meta:
        db_table = 'product_tag'
        unique_together = (('product', 'tag'),)


class Color(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)
    image_url = ImageField(max_length=200, storage=storage.ClientSVGStorage)

    class Meta:
        db_table = 'color'

    def __str__(self):
        return self.name


class ProductColor(Model):
    id = AutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING)
    color = ForeignKey('Color', DO_NOTHING)
    display_color_name = CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'product_color'
        unique_together = (('product', 'display_color_name'),)


class ProductColorImages(Model):
    id = AutoField(primary_key=True)
    product_color = ForeignKey('ProductColor', DO_NOTHING)
    url = CharField(max_length=200)
    sequence = IntegerField()

    class Meta:
        managed = False
        db_table = 'product_color_images'
        unique_together = (('product_color', 'sequence'), ('product_color', 'url'),)


class Size(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=10)

    class Meta:
        db_table = 'size'
        ordering = ['id']

    def __str__(self):
        return self.name


class Option(Model):
    id = BigAutoField(primary_key=True)
    size = ForeignKey('Size', DO_NOTHING)
    price_difference = IntegerField(default=0)
    product_color = ForeignKey('ProductColor', DO_NOTHING)
    display_size_name = CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'option'

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
        managed = False
        db_table = 'style'


class LaundryInformation(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'laundry_information'


class ProductLaundryInformation(Model):
    id = AutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING)
    laundry_information = ForeignKey('LaundryInformation', DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_laundry_information'
        unique_together = (('product', 'laundry_information'),)


class Material(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'material'


class ProductMaterial(Model):
    id = AutoField(primary_key=True)
    product = ForeignKey('Product', DO_NOTHING)
    material = CharField(max_length=20)
    mixing_rate = IntegerField()

    class Meta:
        managed = False
        db_table = 'product_material'
        unique_together = (('product', 'material'),)
