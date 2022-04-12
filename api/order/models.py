from django.db.models import (
    Model, BigAutoField, AutoField, ForeignKey,
    IntegerField, BigIntegerField, CharField, BooleanField, DateTimeField,
    DO_NOTHING
)
from django.utils import timezone


# class PaymentStatus(Model):
#     id = AutoField(primary_key=True)
#     name = CharField(max_length=20)

#     class Meta:
#         db_table = 'payment_status'


class Status(Model):
    id = IntegerField(primary_key=True)
    name = CharField(max_length=20)

    class Meta:
        db_table = 'status'

    def __str__(self):
        return self.name


class ShippingAddress(Model):
    id = BigAutoField(primary_key=True)
    receiver_name = CharField(max_length=20)
    mobile_number = CharField(max_length=11)
    phone_number = CharField(max_length=11, null=True)
    zip_code = CharField(max_length=5)
    base_address = CharField(max_length=200)
    detail_address = CharField(max_length=100)
    shipping_message = CharField(max_length=50)

    class Meta:
        db_table = 'shipping_address'


class Order(Model):
    id = BigAutoField(primary_key=True)
    number = BigIntegerField(unique=True) 
    shopper = ForeignKey('user.Shopper', DO_NOTHING)
    # payment_status = ForeignKey('PaymentStatus', DO_NOTHING)
    shipping_address = ForeignKey('ShippingAddress', DO_NOTHING)
    # total_price = IntegerField()
    # discount_price = IntegerField(default=0)
    # payment_price = IntegerField()
    # refund_price = IntegerField(default=0)
    created_at = DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'order'

    def __set_default_number(self):
        prefix = self.created_at.strftime('%Y%m%d%H%M%S')
        
        for postfix in range(1, 10000):
            self.number = prefix + "%04d" % (postfix)
            if not self.__class__.objects.filter(number=self.number).exists():
                break;

    def save(self, *args, **kwargs):
        if self.number is None:
            self.__set_default_number()

        return super().save(*args, **kwargs)


class OrderItem(Model):
    id = BigAutoField(primary_key=True)
    order = ForeignKey('Order', DO_NOTHING, related_name='items')
    option = ForeignKey('product.Option', DO_NOTHING)
    status = ForeignKey('Status', DO_NOTHING)
    count = IntegerField(default=1)
    # coupon = ForeignKey('shopper.ShopperCoupon', DO_NOTHING, null=True)
    sale_price = IntegerField()
    base_discount_price = IntegerField(default=0)
    membership_discount_price = IntegerField()
    # coupon_discount_price = IntegerField()
    used_point = IntegerField(default=0)
    payment_price = IntegerField()
    earned_point = IntegerField()

    class Meta:
        db_table = 'order_item'


class StatusTransition(Model):
    id = AutoField(primary_key=True)
    previous_status = ForeignKey('Status', DO_NOTHING, related_name='transition_previous_status')
    next_status = ForeignKey('Status', DO_NOTHING, related_name='transition_next_status')
    
    class Meta:
        db_table = 'status_transition'


class StatusLog(Model):
    id = BigAutoField(primary_key=True)
    order_item = ForeignKey('OrderItem', DO_NOTHING, related_name='status_log')
    previous_status = ForeignKey('Status', DO_NOTHING, related_name='previous_status')
    next_status = ForeignKey('Status', DO_NOTHING, related_name='next_status')
    created_at = DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'status_log'


class Cancellation(Model):
    id = BigAutoField(primary_key=True)
    # order_item
    created_at = DateTimeField(default=timezone.now)