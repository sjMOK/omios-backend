import random
from datetime import date, timedelta

from factory import Sequence, LazyAttribute, SubFactory, RelatedFactoryList, post_generation, lazy_attribute
from factory.django import DjangoModelFactory, get_model
from factory.faker import Faker
from factory.fuzzy import FuzzyDecimal, FuzzyInteger

from coupon.test.factories import CouponFactory


def get_factory_password(user):
    return user.username + '_Password'


def get_factory_authentication_data(user):
    return {
        'username': user.username,
        'password': get_factory_password(user),
    }


class MembershipFactory(DjangoModelFactory):
    class Meta:
        model = 'user.Membership'

    name = Sequence(lambda num: f'membership{num}')
    discount_rate = FuzzyDecimal(0, 5, 2)
    qualification = 'qualification'


class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'user.User'
    
    username = Sequence(lambda num: 'user%d' % num)
    password = LazyAttribute(lambda user: get_factory_password(user))


class ShopperFactory(UserFactory):
    class Meta:
        model = 'user.Shopper'

    membership = SubFactory(MembershipFactory)
    name = Faker('name', locale='ko-KR')
    birthday = "2021-11-20"
    gender = Sequence(lambda num: num % 2)
    email = Faker('email')
    mobile_number = Sequence(lambda num: '010%08d' % num)
    point = FuzzyInteger(2000, 5000)


class WholesalerFactory(UserFactory):
    class Meta:
        model = 'user.Wholesaler'

    name = Faker('company', locale='ko-KR')
    mobile_number = Sequence(lambda num: '010%08d' % num)
    phone_number = Sequence(lambda num: '02%08d' % num)
    email = Faker('email')
    company_registration_number= Sequence(lambda num: '%012d' % num)
    business_registration_image_url = Faker('image_url')
    zip_code = Sequence(lambda num: '%05d' % num)
    base_address = Faker('address', locale='ko-KR')
    detail_address = Faker('address_detail', locale='ko-KR')
    is_approved = False


class CartFactory(DjangoModelFactory):
    class Meta:
        model = 'user.Cart'

    option = SubFactory('product.test.factories.OptionFactory')
    shopper = SubFactory(ShopperFactory)
    
    @lazy_attribute
    def count(self):
        return random.randint(1, 100)


class FloorFactory(DjangoModelFactory):
    class Meta:
        model = 'user.Floor'

    name = Sequence(lambda num: '%d층' % num)


class BuildingFactory(DjangoModelFactory):
    class Meta:
        model = 'user.Building'

    name = Sequence(lambda num: '오미오스%d' % num)
    zip_code = '05009'
    base_address = '서울시 광진구 능동로19길 47'

    @post_generation
    def floors(self, create, extracted, **kwargs):
        if create and extracted:
            for floor in extracted:
                self.floors.add(floor)


class BuildingFloorFactory(DjangoModelFactory):
    class Meta:
        model = 'user.BuildingFloor'

    building = SubFactory(BuildingFactory)
    floor = SubFactory(FloorFactory)


class BuildingWithFloorFactory(BuildingFactory):
    floors = RelatedFactoryList(BuildingFloorFactory, 'building', 3)


class ShopperShippingAddressFactory(DjangoModelFactory):
    class Meta:
        model = 'user.ShopperShippingAddress'

    shopper = SubFactory(ShopperFactory)
    name = '집'
    receiver_name = '홍길동'
    receiver_mobile_number = '01011111111'
    receiver_phone_number = '0312223333'
    zip_code = '11111'
    base_address = '서울시 광진구 능동로19길 47'
    detail_address = '518호'
    is_default=False


class PointHistoryFactory(DjangoModelFactory):
    class Meta:
        model = 'user.PointHistory'

    shopper = SubFactory(ShopperFactory)
    point = FuzzyInteger(10000)
    content = 'test'
    order = SubFactory('order.test.factories.OrderFactory', shopper=LazyAttribute(lambda obj: obj.factory_parent.shopper))
    product_name = 'test'


class ShopperCouponFactory(DjangoModelFactory):
    class Meta:
        model = 'user.ShopperCoupon'

    shopper = SubFactory(ShopperFactory)
    coupon = SubFactory(CouponFactory)
    end_date = LazyAttribute(lambda o: o.coupon.end_date)
    is_available = Faker('pybool')

    @lazy_attribute
    def end_date(self):
        if self.coupon.available_period is not None:
            return date.today() + timedelta(days=self.coupon.available_period)
        else:
            return self.coupon.end_date
