from random import randint
from datetime import datetime

from common.test.test_cases import SerializerTestCase, ModelSerializerTestCase
from common.utils import datetime_to_iso
from .factory import get_factory_password, get_factory_authentication_data, UserFactory, ShopperFactory, WholesalerFactory
from ..models import OutstandingToken
from ..serializers import (
    IssuingTokenSerializer, RefreshingTokenSerializer, RefreshToken, MembershipSerializer, 
    UserSerializer, ShopperSerializer, WholesalerSerializer, UserPasswordSerializer,
)


class IssuingTokenSerializerTestCase(SerializerTestCase):
    fixtures = ['membership']
    _serializer_class = IssuingTokenSerializer

    def __get_refresh_token(self, factory):
        self.user = factory()
        serializer = self._get_serializer(data=get_factory_authentication_data(self.user))
        serializer.is_valid()

        return serializer.validated_data['refresh']

    def test_get_user_token(self):
        refresh_token = RefreshToken(self.__get_refresh_token(UserFactory))
        outstanding_token = OutstandingToken.objects.get(jti=refresh_token['jti'])

        self.assertTrue(refresh_token.get('user_type') is None)
        self.assertEqual(refresh_token.token, outstanding_token.token)
        self.assertEqual(outstanding_token.created_at.timetuple(), datetime.fromtimestamp(refresh_token['iat']).timetuple())
        self.assertEqual(outstanding_token.expires_at, datetime.fromtimestamp(refresh_token['exp']))

    def test_get_shopper_token(self):
        refresh_token = RefreshToken(self.__get_refresh_token(ShopperFactory))

        self.assertEqual(refresh_token['user_type'], 'shopper')

    def test_get_wholesaler_token(self):
        pass


class RefreshingTokenSerializerTestCase(SerializerTestCase):
    _serializer_class = RefreshingTokenSerializer

    def test_refresh_token_validation(self):
        user = UserFactory()
        set_up_serializer = IssuingTokenSerializer(data=get_factory_authentication_data(user))
        set_up_serializer.is_valid()
        serializer = self._get_serializer(data={'refresh': set_up_serializer.validated_data['refresh']})
        serializer.is_valid()

        self.assertIsNotNone(OutstandingToken.objects.get(token=serializer.validated_data['refresh']))


class MembershipSerializerTestCase(ModelSerializerTestCase):
    fixtures = ['membership']
    _serializer_class = MembershipSerializer

    def test_model_instance_serialization(self):
        membership = self._serializer_class.Meta.model.objects.get(id=1)
        self._test_model_instance_serialization(membership, {
            'id': membership.id,
            'name': membership.name,
        })


class UserSerializerTestCase(ModelSerializerTestCase):
    _serializer_class = UserSerializer

    @classmethod
    def setUpTestData(cls):
        cls._user = UserFactory()

    def setUp(self):
        self.test_data = {
            'username': 'username'
        }

    def _get_serializer(self, password=None, **kwargs):
        if password is not None:
            self.test_data['password'] = password

        return super()._get_serializer(data=self.test_data, **kwargs)

    def test_model_instance_serialization(self):
        self._test_model_instance_serialization(self._user, {
            'id': self._user.id,
            'last_login': self._user.last_login,
            'username': self._user.username,
            'is_admin': self._user.is_admin,
            'is_active': self._user.is_active,
            'last_update_password': datetime_to_iso(self._user.last_update_password),
            'created_at': datetime_to_iso(self._user.created_at),
            'deleted_at': datetime_to_iso(self._user.deleted_at),
        })

    def test_lowercase_number_password_regex_validation(self):
        serializer = self._get_serializer('username00')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('password' in serializer.errors)
        self.assertEqual(str(serializer.errors['password'][0]), 'This value does not match the required pattern.')

    def test_uppercase_number_password_regex_validation(self):
        serializer = self._get_serializer('USERNAME00')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('password' in serializer.errors)
        self.assertEqual(str(serializer.errors['password'][0]), 'This value does not match the required pattern.')

    def test_lowercase_uppercase_password_regex_validation(self):
        serializer = self._get_serializer('usernameUSERNAME')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('password' in serializer.errors)
        self.assertEqual(str(serializer.errors['password'][0]), 'This value does not match the required pattern.')

    def test_password_similarity_validation(self):
        serializer = self._get_serializer('Username00')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('non_field_errors' in serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]), 'The similarity between password and username is too large.')

    def test_update(self):
        original_password = get_factory_password(self._user)
        serializer = self._get_serializer(instance=self._user, partial=True)
        serializer.is_valid()
        self._user = serializer.save()

        self.assertEqual(self._user.username, self.test_data['username'])
        self.assertTrue(self._user.check_password(original_password))


class ShopperSerializerTestCase(ModelSerializerTestCase):
    fixtures = ['membership']
    _serializer_class = ShopperSerializer

    def test_model_instance_serialization(self):
        shopper = ShopperFactory()
        self._test_model_instance_serialization(shopper, {
            **UserSerializer(instance=shopper).data,
            'membership': MembershipSerializer(instance=shopper.membership).data,
            'name': shopper.name,
            'nickname': shopper.nickname,
            'phone': shopper.phone,
            'email': shopper.email,
            'gender': shopper.gender,
            'birthday': shopper.birthday,
            'height': shopper.height,
            'weight': shopper.weight,
        })


class WholesalerSerializerTestCase(ModelSerializerTestCase):
    pass


class UserPasswordSerializerTestCase(SerializerTestCase):
    _serializer_class = UserPasswordSerializer

    def setUp(self):
        self.user = UserFactory()
        self.test_data = {
            'current_password': get_factory_password(self.user),
            'new_password': self.user.username + '_New_Password',
        }

    def _get_serializer(self, current_password=None, new_password=None, **kwargs):
        if current_password is not None:
            self.test_data['current_password'] = current_password
        if new_password is not None:
            self.test_data['new_password'] = new_password

        return super()._get_serializer(instance=self.user, data=self.test_data)

    def test_current_password_validation(self):
        serializer = self._get_serializer('weird_password')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('non_field_errors' in serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]), 'current password does not correct.')
        
    def test_same_new_password_validation(self):
        serializer = self._get_serializer(new_password=self.test_data['current_password'])

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('non_field_errors' in serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]), 'new password is same as the current password.')
        
    def test_update(self):
        token_num = randint(3, 10)
        for _ in range(token_num):
            set_up_serializer = IssuingTokenSerializer(data=get_factory_authentication_data(self.user))
            set_up_serializer.is_valid()
        serializer = self._get_serializer()
        serializer.is_valid()
        self.user = serializer.save()

        self.assertTrue(self.user.check_password(self.test_data['new_password']))
        self.assertEqual(len(OutstandingToken.objects.filter(user_id=self.user.id, blacklistedtoken__isnull=False)), token_num)
