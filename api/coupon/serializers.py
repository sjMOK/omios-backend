from datetime import date

from rest_framework.serializers import (
    ModelSerializer,
)
from rest_framework.exceptions import ValidationError

from .models import Coupon


class CouponSerializer(ModelSerializer):
    class Meta:
        model = Coupon
        exclude = ['products', 'sub_categories']
        extra_kwargs = {
            'discount_rate': {'min_value': 0, 'max_value': 100},
            'discount_price': {'min_value': 0, 'max_value': 1000000},
            'minimum_order_price': {'min_value': 0, 'max_value': 1000000},
            'maximum_discount_price': {'min_value': 0, 'max_value': 1000000},
            'available_period': {'min_value': 0},
        }

    def to_representation(self, instance):
        result = super().to_representation(instance)

        if result['id'] in self.context.get('owned_coupon_id_list', []):
            result['coupon_owned'] = True
        else:
            result['coupon_owned'] = False

        return result

    def validate_end_date(self, value):
        if value < date.today():
            raise ValidationError('Please check the end_date of the coupon.')

        return value

    def validate(self, attrs):
        discount_rate = attrs.get('discount_rate', None)
        discount_price = attrs.get('discount_price', None)
        self.__validate_discount_rate_and_discount_price_exclusive_or(discount_rate, discount_price)

        start_date = attrs.get('start_date', None)
        end_date = attrs.get('end_date', None)
        available_period = attrs.get('available_period', None)
        self.__validate_expiration_data(start_date, end_date, available_period)

        return attrs

    def __validate_discount_rate_and_discount_price_exclusive_or(self, discount_rate, discount_price):
        if not (bool(discount_rate) ^ bool(discount_price)):
            raise ValidationError('Only one of discount_rate or discount_price must exist.')

    def __validate_expiration_data(self, start_date, end_date, available_period):
        self.__validate_expiration_data_exclusive_or(start_date, end_date, available_period)
        if available_period is None:
            self.__validate_start_date_and_end_date(start_date, end_date)

    def __validate_expiration_data_exclusive_or(self, start_date, end_date, available_period):
        date_data = [data for data in [start_date, end_date] if data is not None]

        if not (bool(date_data) ^ bool(available_period)):
            raise ValidationError('Only one of date or available_period must exist.')

    def __validate_start_date_and_end_date(self, start_date, end_date):
        if not (start_date and end_date):
            raise ValidationError('Both start_date and end_date must exist.')
        elif start_date > end_date:
            raise ValidationError('The start date must be before the end date.')
