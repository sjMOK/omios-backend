from datetime import date, timedelta

from rest_framework.exceptions import ValidationError

from common.test.test_cases import SerializerTestCase
from common.utils import datetime_to_iso
from product.test.factories import ProductFactory, SubCategoryFactory
from user.test.factories import ShopperFactory, ShopperCouponFactory
from .factories import CouponFactory, CouponClassificationFactory
from ..serializers import COUPON_PRODUCT_MAX_LENGTH, COUPON_SUBCATEGORY_MAX_LENGTH, CouponClassificationSerializer, CouponSerializer


class CouponClassificationSerializerTestCase(SerializerTestCase):
    _serializer_class = CouponClassificationSerializer

    def test_model_instance_serialization(self):
        coupon_classification = CouponClassificationFactory()
        self._test_model_instance_serialization(coupon_classification, {
            'id': coupon_classification.id,
            'name': coupon_classification.name,
        })


class CouponSerializerTestCase(SerializerTestCase):
    _serializer_class = CouponSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__coupon_classification = CouponClassificationFactory()
        cls.__coupon = CouponFactory(classification=cls.__coupon_classification)
        cls._test_data = {
            'name': 'super coupon',
            'discount_price': 10000,
            'start_date': date.today() - timedelta(weeks=1),
            'end_date': date.today() + timedelta(weeks=1),
            'is_auto_issue': False,
            'classification': cls.__coupon_classification.id,
        }

    def test_model_instance_serialization(self):
        self._test_model_instance_serialization(self.__coupon, {
            'id': self.__coupon.id,
            'name': self.__coupon.name,
            'discount_rate': self.__coupon.discount_rate,
            'discount_price': self.__coupon.discount_price,
            'minimum_order_price': self.__coupon.minimum_order_price,
            'maximum_discount_price': self.__coupon.maximum_discount_price,
            'start_date': datetime_to_iso(self.__coupon.start_date),
            'end_date': datetime_to_iso(self.__coupon.end_date),
            'available_period': self.__coupon.available_period,
            'is_auto_issue': self.__coupon.is_auto_issue,
            'classification': self.__coupon.classification.id,
            'coupon_owned': False,
        })

    def test_model_instance_serialization_coupon_owned_true(self):
        shopper = ShopperFactory()
        ShopperCouponFactory(shopper=shopper, coupon=self.__coupon)

        owned_coupon_id_list = list(shopper.coupons.all().values_list('id', flat=True))
        context = {'owned_coupon_id_list': owned_coupon_id_list}

        self._test_model_instance_serialization(self.__coupon, {
            'id': self.__coupon.id,
            'name': self.__coupon.name,
            'discount_rate': self.__coupon.discount_rate,
            'discount_price': self.__coupon.discount_price,
            'minimum_order_price': self.__coupon.minimum_order_price,
            'maximum_discount_price': self.__coupon.maximum_discount_price,
            'start_date': datetime_to_iso(self.__coupon.start_date),
            'end_date': datetime_to_iso(self.__coupon.end_date),
            'available_period': self.__coupon.available_period,
            'is_auto_issue': self.__coupon.is_auto_issue,
            'classification': self.__coupon.classification.id,
            'coupon_owned': True,
        }, context)

    def test_raise_validation_error_discount_rate_and_discount_price_are_not_exclusive_or(self):
        self._test_data['discount_rate'] = 10
        self._test_serializer_raise_validation_error(
            'Only one of discount_rate or discount_price must exist.',
            data=self._test_data
        )

    def test_raise_validation_error_end_date_less_than_today(self):
        self._test_data['end_date'] = date.today() - timedelta(days=1)
        self._test_serializer_raise_validation_error(
            'Please check the end_date of the coupon.',
            data=self._test_data
        )
    
    def test_raise_validation_error_start_date_greater_than_today(self):
        self._test_data['start_date'] = self._test_data['end_date'] + timedelta(days=1)
        self._test_serializer_raise_validation_error(
            'The start date must be before the end date.',
            data=self._test_data
        )

    def test_raise_validation_error_only_start_date(self):
        self._test_data.pop('end_date')
        self._test_serializer_raise_validation_error(
            'Both start_date and end_date must exist.',
            data=self._test_data
        )

    def test_raise_validation_error_only_end_date(self):
        self._test_data.pop('start_date')
        self._test_serializer_raise_validation_error(
            'Both start_date and end_date must exist.',
            data=self._test_data
        )

    def test_raise_validation_error_expiration_data_is_not_exclusive_or(self):
        self._test_data['available_period'] = 14
        self._test_serializer_raise_validation_error(
            'Only one of date or available_period must exist.',
            data=self._test_data
        )
    
    def test_raise_validation_error_start_date_and_available_period_passed_together(self):
        self._test_data['available_period'] = 14
        self._test_data.pop('end_date')
        self._test_serializer_raise_validation_error(
            'Only one of date or available_period must exist.',
            data=self._test_data
        )

    def test_raise_validation_error_end_date_and_available_period_passed_together(self):
        self._test_data['available_period'] = 14
        self._test_data.pop('start_date')
        self._test_serializer_raise_validation_error(
            'Only one of date or available_period must exist.',
            data=self._test_data
        )
