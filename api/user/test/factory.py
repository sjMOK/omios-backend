from factory import Sequence, LazyAttribute
from factory.django import DjangoModelFactory
from factory.faker import Faker


def get_factory_password(user):
    return user.username + '_Password'


def get_factory_authentication_data(user):
    return {
        'username': user.username,
        'password': get_factory_password(user),
    }


class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'user.User'
    
    username = Sequence(lambda num: 'user%d' % num)
    password = LazyAttribute(lambda user: get_factory_password(user))


class ShopperFactory(UserFactory):
    class Meta:
        model = 'user.Shopper'

    name = Faker('name', locale='ko-KR')
    birthday = "2021-11-20"
    gender = Sequence(lambda num: num % 2)
    email = LazyAttribute(lambda shopper: '%s@omios.com' % shopper.username)
    phone = Sequence(lambda num: '010%08d' % num)


class WholesalerFactory(UserFactory):
    class Meta:
        model = 'user.Wholesaler'