from rest_framework.serializers import (
    ModelSerializer
)

from .models import Coupon


class CouponSerializer(ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        extra_kwargs = {
            'discount_rate': {'min_value': 0, 'max_value': 100},
            'discount_price': {'min_value': 1, 'max_value': 1000000},
            'minimum_order_price': {'min_value': 0},
            'maximum_discount_price': {'min_value': 0},
            'available_period': {'min_value': 0},
        }
