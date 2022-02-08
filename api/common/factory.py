from factory import Sequence, LazyAttribute
from factory.django import DjangoModelFactory


def get_factory_password(user):
    return user.username + '_Password'


class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'user.User'
    
    username = Sequence(lambda num: 'user%d' % num)
    password = LazyAttribute(lambda user: get_factory_password(user))


class ShopperFactory(UserFactory):
    class Meta:
        model = 'user.Shopper'

    name = "test"
    birthday = "2017-01-01"
    gender = 1
    email = "testemail@naver.com"
    phone = "01012345678"


class WholesalerFactory(UserFactory):
    class Meta:
        model = 'user.Wholesaler'