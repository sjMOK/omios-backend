from datetime import date, timedelta

from common.test.test_cases import ModelTestCase
from ..models import CouponClassification, Coupon
from .factories import CouponClassificationFactory


class CouponClassificationTestCase(ModelTestCase):
    _model_class = CouponClassification

    def test_create(self):
        self._test_data = {
            'name': '전 상품 쿠폰',
        }
        coupon_classification = self._get_model_after_creation()
        
        self.assertEqual(coupon_classification.name, self._test_data['name'])


class CouponTestCase(ModelTestCase):
    _model_class = Coupon

    @classmethod
    def setUpTestData(cls):
        coupon_classification = CouponClassificationFactory()
        cls._test_data = {
            'classification': coupon_classification,
            'name': '오픈 기념 쿠폰',
            'discount_rate': 10,
            'minimum_product_price': 10000,
            'maximum_discount_price': 100000,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
            'is_auto_issue': True,
        }

    def test_create(self):
        coupon = self._get_model_after_creation()

        self.assertEqual(coupon.classification, self._test_data['classification'])
        self.assertEqual(coupon.name, self._test_data['name'])
        self.assertEqual(coupon.discount_rate, self._test_data['discount_rate'])
        self.assertEqual(coupon.minimum_product_price, self._test_data['minimum_product_price'])
        self.assertEqual(coupon.maximum_discount_price, self._test_data['maximum_discount_price'])
        self.assertEqual(coupon.start_date, self._test_data['start_date'])
        self.assertEqual(coupon.end_date, self._test_data['end_date'])
        self.assertEqual(coupon.is_auto_issue, self._test_data['is_auto_issue'])

    def test_create_default_value(self):
        self._test_data.pop('minimum_product_price')
        coupon = self._get_model_after_creation()

        self.assertEqual(coupon.minimum_product_price, 0)
