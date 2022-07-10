from datetime import date

from rest_framework.serializers import (
    ModelSerializer, PrimaryKeyRelatedField,
)
from rest_framework.exceptions import ValidationError

from product.models import Product, SubCategory
from .models import CouponClassification, Coupon

COUPON_PRODUCT_MAX_LENGTH = 1000
COUPON_SUBCATEGORY_MAX_LENGTH = 20


class CouponClassificationSerializer(ModelSerializer):
    class Meta:
        model = CouponClassification
        fields = '__all__'


class CouponSerializer(ModelSerializer):
    products = PrimaryKeyRelatedField(write_only=True, queryset=Product.objects.filter(on_sale=True), many=True, required=False)
    sub_categories = PrimaryKeyRelatedField(write_only=True, queryset=SubCategory.objects.all(), many=True, required=False)
    class Meta:
        model = Coupon
        fields = '__all__'
        extra_kwargs = {
            'discount_rate': {'min_value': 0, 'max_value': 100},
            'discount_price': {'min_value': 0, 'max_value': 1000000},
            'minimum_product_price': {'min_value': 0, 'max_value': 1000000},
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

    def validate_products(self, value):
        if len(value) > COUPON_PRODUCT_MAX_LENGTH:
            raise ValidationError('You can register up to 1000 products per coupon.')

        return value

    def validate_sub_categories(self, value):
        if len(value) > COUPON_SUBCATEGORY_MAX_LENGTH:
            raise ValidationError('You can register up to 20 categories per coupon.')

        return value

    def validate(self, attrs):
        # todo
        # 정액 할인일 경우 (discount_price) 최대 할인 금액 선택 불가능 validation

        attrs = self.__validate_classification(attrs)

        discount_rate = attrs.get('discount_rate', None)
        discount_price = attrs.get('discount_price', None)
        self.__validate_discount_rate_and_discount_price_exclusive_or(discount_rate, discount_price)

        start_date = attrs.get('start_date', None)
        end_date = attrs.get('end_date', None)
        available_period = attrs.get('available_period', None)
        self.__validate_expiration_data(start_date, end_date, available_period)

        return attrs

    def __validate_classification(self, attrs):
        classification = attrs['classification']
        if classification.id in [1, 5]:
            attrs.pop('products', None)
            attrs.pop('sub_categories', None)
        elif classification.id == 2:
            if 'products' not in attrs:
                raise ValidationError('You must pass product_id list.')
            attrs.pop('sub_categories', None)
        elif classification.id == 3:
            if 'sub_categories' not in attrs:
                raise ValidationError('You must pass sub_category_id list.')
            attrs.pop('products', None)
        elif classification.id == 4:
            attrs.pop('products', None)
            attrs.pop('sub_categories', None)

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

    # todo
    # is_auto_issue 자동 발급
    # transaction