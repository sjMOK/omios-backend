from django.db.models import (
    Model, AutoField, CharField, IntegerField, DateField, BooleanField, ForeignKey, ManyToManyField,
    DO_NOTHING,
)


class CouponClassification(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'coupon_classification'

    def __str__(self):
        return self.name

class Coupon(Model):
    id = AutoField(primary_key=True)
    classification = ForeignKey('CouponClassification', DO_NOTHING)
    name = CharField(max_length=100)
    discount_rate = IntegerField(null=True)
    discount_price = IntegerField(null=True)
    minimum_order_price = IntegerField(default=0)
    maximum_discount_price = IntegerField(null=True)
    start_date = DateField(null=True)
    end_date = DateField(null=True)
    available_period = IntegerField(null=True)
    is_auto_issue = BooleanField()

    products = ManyToManyField('product.Product', db_table='coupon_product')
    sub_categories = ManyToManyField('product.SubCategory', through='CouponSubCategory')

    class Meta:
        db_table = 'coupon'
        ordering = ['-id']

    def __str__(self):
        return self.name


class CouponSubCategory(Model):
    id = AutoField(primary_key=True)
    coupon = ForeignKey('Coupon', DO_NOTHING)
    sub_category = ForeignKey('product.SubCategory', DO_NOTHING)

    class Meta:
        db_table = 'coupon_sub_category'
