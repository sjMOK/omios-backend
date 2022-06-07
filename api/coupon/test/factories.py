from datetime import date, timedelta

from factory import SubFactory
from factory.fuzzy import FuzzyInteger
from factory.django import DjangoModelFactory
from factory.faker import Faker


class CouponClassificationFactory(DjangoModelFactory):
    class Meta:
        model = 'coupon.CouponClassification'

    name = Faker('word')


class CouponFactory(DjangoModelFactory):
    class Meta:
        model = 'coupon.Coupon'

    classification = SubFactory(CouponClassificationFactory)
    name = Faker('word')
    discount_rate = FuzzyInteger(10, 30)
    minimum_order_price = FuzzyInteger(5000, 10000)
    maximum_discount_price = FuzzyInteger(100000, 200000)
    start_date = date.today()
    end_date = date.today() + timedelta(days=30)
    is_auto_issue = Faker('pybool')
    