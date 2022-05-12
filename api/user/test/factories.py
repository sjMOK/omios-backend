from factory import Sequence, LazyAttribute, SubFactory, RelatedFactoryList, post_generation
from factory.django import DjangoModelFactory, get_model
from factory.faker import Faker
from factory.fuzzy import FuzzyDecimal, FuzzyInteger


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
    discount_rate = FuzzyDecimal(0, 5, 1)
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
