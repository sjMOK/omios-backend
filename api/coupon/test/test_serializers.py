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
    fixtures = ['coupon_classification']

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

        products = ProductFactory.create_batch(size=2)
        sub_categories = SubCategoryFactory.create_batch(size=2)

        cls.__product_id_list = [product.id for product in products]
        cls.__sub_category_id_list = [sub_category.id for sub_category in sub_categories]

    def test_model_instance_serialization(self):
        self._test_model_instance_serialization(self.__coupon, {
            'id': self.__coupon.id,
            'name': self.__coupon.name,
            'discount_rate': self.__coupon.discount_rate,
            'discount_price': self.__coupon.discount_price,
            'minimum_product_price': self.__coupon.minimum_product_price,
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
            'minimum_product_price': self.__coupon.minimum_product_price,
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
            'Only one of discount_rate or discount_price must exist.'
        )

    def test_raise_validation_error_end_date_less_than_today(self):
        self._test_data['end_date'] = date.today() - timedelta(days=1)
        self._test_serializer_raise_validation_error(
            'Please check the end_date of the coupon.'
        )
    
    def test_raise_validation_error_start_date_greater_than_today(self):
        self._test_data['start_date'] = self._test_data['end_date'] + timedelta(days=1)
        self._test_serializer_raise_validation_error(
            'The start date must be before the end date.'
        )

    def test_raise_validation_error_only_start_date(self):
        self._test_data.pop('end_date')
        self._test_serializer_raise_validation_error(
            'Both start_date and end_date must exist.'
        )

    def test_raise_validation_error_only_end_date(self):
        self._test_data.pop('start_date')
        self._test_serializer_raise_validation_error(
            'Both start_date and end_date must exist.'
        )

    def test_raise_validation_error_expiration_data_is_not_exclusive_or(self):
        self._test_data['available_period'] = 14
        self._test_serializer_raise_validation_error(
            'Only one of date or available_period must exist.'
        )
    
    def test_raise_validation_error_start_date_and_available_period_passed_together(self):
        self._test_data['available_period'] = 14
        self._test_data.pop('end_date')
        self._test_serializer_raise_validation_error(
            'Only one of date or available_period must exist.'
        )

    def test_raise_validation_error_end_date_and_available_period_passed_together(self):
        self._test_data['available_period'] = 14
        self._test_data.pop('start_date')
        self._test_serializer_raise_validation_error(
            'Only one of date or available_period must exist.'
        )

    def test_validate_classification_all_products(self):
        self._test_data['classification'] = 1
        self._test_data['products'] = self.__product_id_list
        self._test_data['sub_categories'] = self.__sub_category_id_list
        serializer = self._get_serializer_after_validation()

        self.assertTrue('products' not in serializer.validated_data)
        self.assertTrue('sub_categories' not in serializer.validated_data)

    def test_validate_classification_partial_products(self):
        self._test_data['classification'] = 2
        self._test_data['products'] = self.__product_id_list
        self._test_data['sub_categories'] = self.__sub_category_id_list
        serializer = self._get_serializer_after_validation()

        self.assertTrue('products' in serializer.validated_data)
        self.assertTrue('sub_categories' not in serializer.validated_data)

    def test_raise_validation_error_partial_products_coupon_does_not_pass_product_id_list(self):
        self._test_data['classification'] = 2

        self._test_serializer_raise_validation_error(
            'You must pass product_id list.'
        )

    def test_raise_validation_error_sub_category_coupon_does_not_pass_sub_category_id_list(self):
        self._test_data['classification'] = 3

        self._test_serializer_raise_validation_error(
            'You must pass sub_category_id list.'
        )

    def test_validate_classification_sub_category(self):
        self._test_data['classification'] = 3
        self._test_data['products'] = self.__product_id_list
        self._test_data['sub_categories'] = self.__sub_category_id_list
        serializer = self._get_serializer_after_validation()

        self.assertTrue('products' not in serializer.validated_data)
        self.assertTrue('sub_categories' in serializer.validated_data)

    def test_validate_classification_exhibition(self):
        self._test_data['classification'] = 4
        self._test_data['products'] = self.__product_id_list
        self._test_data['sub_categories'] = self.__sub_category_id_list
        serializer = self._get_serializer_after_validation()

        self.assertTrue('products' not in serializer.validated_data)
        self.assertTrue('sub_categories' not in serializer.validated_data)

    def test_validate_classification_signup(self):
        self._test_data['classification'] = 5
        self._test_data['products'] = self.__product_id_list
        self._test_data['sub_categories'] = self.__sub_category_id_list
        serializer = self._get_serializer_after_validation()

        self.assertTrue('products' not in serializer.validated_data)
        self.assertTrue('sub_categories' not in serializer.validated_data)

    def test_validate_products(self):
        product_id_list = list(range(COUPON_PRODUCT_MAX_LENGTH + 1))
        serializer = self._get_serializer()

        self.assertRaisesRegexp(
            ValidationError,
            'You can register up to {} products per coupon.'.format(COUPON_PRODUCT_MAX_LENGTH),
            serializer.validate_products,
            product_id_list
        )

    def test_validate_sub_categories(self):
        sub_category_id_list = list(range(COUPON_SUBCATEGORY_MAX_LENGTH + 1))
        serializer = self._get_serializer()

        self.assertRaisesRegexp(
            ValidationError,
            'You can register up to {} categories per coupon.'.format(COUPON_SUBCATEGORY_MAX_LENGTH),
            serializer.validate_sub_categories,
            sub_category_id_list
        )
