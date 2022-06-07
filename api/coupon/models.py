from django.db.models import (
    Model, AutoField, CharField, ForeignKey, IntegerField, DateField, BooleanField,
    DO_NOTHING,
)


class CouponClassification(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True, max_length=20)

    class Meta:
        db_table = 'coupon_classification'


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

    class Meta:
        db_table = 'coupon'


class CouponProduct(Model):
    # ManyToManyField로 대체
    id = AutoField(primary_key=True)
    coupon = ForeignKey('Coupon', DO_NOTHING)
    product = ForeignKey('product.Product', DO_NOTHING)

    class Meta:
        db_table = 'coupon_product'


class CouponSubCategory(Model):
    # ManyToManyField로 대체
    id = AutoField(primary_key=True)
    coupon = ForeignKey('Coupon', DO_NOTHING)
    sub_category = ForeignKey('product.SubCategory', DO_NOTHING)

    class Meta:
        db_table = 'coupon_sub_category'
