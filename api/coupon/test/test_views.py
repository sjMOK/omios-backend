from datetime import date, timedelta
import random

from django.db.models import Q

from common.test.test_cases import ViewTestCase
from coupon.models import CouponClassification, Coupon
from product.test.factories import ProductFactory
from user.test.factories import UserFactory, ShopperCouponFactory
from .factories import CouponClassificationFactory, CouponFactory
from ..serializers import CouponClassificationSerializer, CouponSerializer


class GetCouponClassificationTestCase(ViewTestCase):
    _url = '/coupons/classifications'

    def setUp(self):
        CouponClassificationFactory.create_batch(size=2)

        self._user = UserFactory(is_admin=True)
        self._set_authentication()

    def test(self):
        queryset = CouponClassification.objects.all()
        serializer = CouponClassificationSerializer(queryset, many=True)
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data, serializer.data)


class CouponViewSetTestCase(ViewTestCase):
    _url = '/coupons'

    @classmethod
    def setUpTestData(cls):
        cls.__admin_user = UserFactory(is_admin=True)
        cls.__coupon_classification = CouponClassificationFactory()
        CouponFactory(classification=cls.__coupon_classification, is_auto_issue=False)
        CouponFactory(classification=cls.__coupon_classification, end_date=date.today() - timedelta(days=1), is_auto_issue=False)
        CouponFactory(classification=cls.__coupon_classification, is_auto_issue=True)
        CouponFactory(classification=cls.__coupon_classification, start_date=None, end_date=None, available_period=14, is_auto_issue=False)

    def test_create(self):
        self._user = self.__admin_user
        self._test_data = {
            'name': 'super coupon',
            'discount_price': 10000,
            'start_date': date.today() - timedelta(weeks=1),
            'end_date': date.today() + timedelta(weeks=1),
            'is_auto_issue': False,
            'classification': self.__coupon_classification.id,
        }
        self._set_authentication()
        self._post()
        
        self._assert_success_and_serializer_class(CouponSerializer)

    def test_list_shopper(self):
        self._set_shopper()
        self._set_authentication()
        for coupon in Coupon.objects.all():
            ShopperCouponFactory(shopper=self._user, coupon=coupon)
        ShopperCouponFactory(coupon=CouponFactory(classification=self.__coupon_classification, is_auto_issue=False))

        queryset = Coupon.objects.filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True), is_auto_issue=False)
        owned_coupon_id_list = list(self._user.coupons.all().values_list('id', flat=True))
        context = {'owned_coupon_id_list': owned_coupon_id_list}
        serializer = CouponSerializer(queryset, many=True, context=context)

        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_list_anonymous_user(self):
        queryset = Coupon.objects.filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True), is_auto_issue=False)
        serializer = CouponSerializer(queryset, many=True, context={})

        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_list_admin_user(self):
        self._user = self.__admin_user
        self._set_authentication()

        queryset = Coupon.objects.all()
        serializer = CouponSerializer(queryset, many=True, context={})

        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_list_with_product_id_query_parameter(self):
        CouponFactory.create_batch(size=5, classification=self.__coupon_classification, is_auto_issue=False)
        queryset = Coupon.objects.filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True), is_auto_issue=False)
        
        product = ProductFactory()
        product_coupons = random.sample(list(queryset.all()), 2)
        for coupon in product_coupons:
            coupon.products.add(product)

        sub_category_coupons = random.sample(list(queryset.all()), 2)
        for coupon in sub_category_coupons:
            coupon.sub_categories.add(product.sub_category)

        filter_condition = Q(products=product) | Q(sub_categories=product.sub_category_id)
        filtered_queryset = queryset.filter(filter_condition)
        
        serializer = CouponSerializer(filtered_queryset, many=True, context={})

        self._get({'product': product.id})

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)
