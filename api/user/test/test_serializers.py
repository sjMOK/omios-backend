from random import randint
from datetime import datetime
from rest_framework.test import APITestCase, APITransactionTestCase

from common.test import SerializerTestCase
from common.factory import get_factory_password, UserFactory, ShopperFactory, WholesalerFactory
from ..models import OutstandingToken
from ..serializers import UserAccessTokenSerializer, UserPasswordSerializer, UserRefreshTokenSerializer, RefreshToken, UserSerializer

from django.test import tag

def get_authentication_data(user):
    return {
        'username': user.username,
        'password': get_factory_password(user),
    }


class UserTokenSerializerTest(APITestCase):
    fixtures = ['membership']
    __serializer_class = UserAccessTokenSerializer

    def __get_refresh_token(self, factory):
        self.user = factory()
        serializer = self.__serializer_class(data=get_authentication_data(self.user))
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


class UserRefreshTokenSerializerTest(APITestCase):
    __serializer_class = UserRefreshTokenSerializer

    def test_refresh_token_validation(self):
        user = UserFactory()
        set_up_serializer = UserAccessTokenSerializer(data=get_authentication_data(user))
        set_up_serializer.is_valid()
        serializer = self.__serializer_class(data={'refresh': set_up_serializer.validated_data['refresh']})
        serializer.is_valid()

        self.assertIsNotNone(OutstandingToken.objects.get(token=serializer.validated_data['refresh']))


class UserSerializerTest(APITestCase):
    __serializer_class = UserSerializer

    def setUp(self):
        self.test_data = {
            'username': 'username'
        }

    def __get_serializer(self, password=None, **kwargs):
        if password is not None:
            self.test_data['password'] = password

        return self.__serializer_class(data=self.test_data, **kwargs)

    def test_password_regex_validation(self):
        test_datas = ['username00', 'USERNAME00', 'usernameUSERNAME']
        for test_data in test_datas:
            serializer = self.__get_serializer(test_data)

            self.assertTrue(not serializer.is_valid())
            self.assertTrue('password' in serializer.errors)
            self.assertEqual(str(serializer.errors['password'][0]), 'This value does not match the required pattern.')

    def test_password_similarity_validation(self):
        serializer = self.__get_serializer('Username00')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('non_field_errors' in serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]), 'The similarity between password and username is too large.')

    def test_update(self):
        user = UserFactory()
        original_password = get_factory_password(user)
        serializer = self.__get_serializer(instance=user, partial=True)
        serializer.is_valid()
        user = serializer.save()

        self.assertEqual(user.username, self.test_data['username'])
        self.assertTrue(user.check_password(original_password))


class UserPasswordSerializerTest(APITestCase):
    __serializer_class = UserPasswordSerializer

    def setUp(self):
        self.user = UserFactory()
        self.test_data = {
            'current_password': get_factory_password(self.user),
            'new_password': self.user.username + '_New_Password',
        }

    def __get_serializer(self, current_password=None, new_password=None):
        if current_password is not None:
            self.test_data['current_password'] = current_password
        if new_password is not None:
            self.test_data['new_password'] = new_password

        return self.__serializer_class(instance=self.user, data=self.test_data)

    def test_current_password_validation(self):
        serializer = self.__get_serializer('weird_password')

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('non_field_errors' in serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]), 'current password does not correct.')
        
    def test_same_new_password_validation(self):
        serializer = self.__get_serializer(new_password=self.test_data['current_password'])

        self.assertTrue(not serializer.is_valid())
        self.assertTrue('non_field_errors' in serializer.errors)
        self.assertEqual(str(serializer.errors['non_field_errors'][0]), 'new password is same as the current password.')
        
    def test_update(self):
        token_num = randint(3, 10)
        for i in range(token_num):
            serializer = UserAccessTokenSerializer(data=get_authentication_data(self.user))
            serializer.is_valid()
        serializer = self.__get_serializer()
        serializer.is_valid()
        self.user = serializer.save()

        self.assertTrue(self.user.check_password(self.test_data['new_password']))
        self.assertEqual(len(OutstandingToken.objects.filter(user_id=self.user.id, blacklistedtoken__isnull=False)), token_num)
