from datetime import datetime

from common.test.test_cases import FunctionTestCase, SerializerTestCase
from common.utils import gmt_to_kst, datetime_to_iso
from .factory import (
    get_factory_password, get_factory_authentication_data, 
    MembershipFactory, UserFactory, ShopperFactory, WholesalerFactory, BuildingWithFloorFactory,
    ShopperShippingAddressFactory,
)
from ..models import OutstandingToken, Membership, Floor
from ..serializers import (
    get_token_time,
    IssuingTokenSerializer, RefreshingTokenSerializer, RefreshToken, MembershipSerializer, 
    UserSerializer, ShopperSerializer, WholesalerSerializer, BuildingSerializer, UserPasswordSerializer,
    ShopperShippingAddressSerializer, PointHistorySerializer,
)


class GetTokenTimeTestCase(FunctionTestCase):
    _function = get_token_time

    def test(self):
        token = RefreshToken()
        expected_result = {
            'created_at': gmt_to_kst(token.current_time),
            'expires_at': gmt_to_kst(datetime.utcfromtimestamp(token['exp'])),
        }

        self.assertDictEqual(self._call_function(token), expected_result)


class IssuingTokenSerializerTestCase(SerializerTestCase):
    _serializer_class = IssuingTokenSerializer

    def __get_refresh_token(self, user):
        serializer = self._get_serializer_after_validation(data=get_factory_authentication_data(user))

        return RefreshToken(serializer.validated_data['refresh'])

    def test_get_user_token(self):
        refresh_token = self.__get_refresh_token(UserFactory())
        outstanding_token = OutstandingToken.objects.get(jti=refresh_token['jti'])

        self.assertTrue(refresh_token.get('user_type') is None)
        self.assertEqual(refresh_token.token, outstanding_token.token)
        self.assertEqual(outstanding_token.created_at.timetuple(), datetime.fromtimestamp(refresh_token['iat']).timetuple())
        self.assertEqual(outstanding_token.expires_at, datetime.fromtimestamp(refresh_token['exp']))

    def test_get_shopper_token(self):
        refresh_token = self.__get_refresh_token(ShopperFactory())

        self.assertEqual(refresh_token['user_type'], 'shopper')

    def test_get_wholesaler_token(self):
        pass


class RefreshingTokenSerializerTestCase(SerializerTestCase):
    _serializer_class = RefreshingTokenSerializer

    def test_refresh_token_validation(self):
        serializer = self._get_serializer_after_validation(data={'refresh': str(RefreshToken.for_user(UserFactory()))})

        self.assertIsNotNone(OutstandingToken.objects.get(token=serializer.validated_data['refresh']))


class MembershipSerializerTestCase(SerializerTestCase):
    _serializer_class = MembershipSerializer

    def test_model_instance_serialization(self):
        membership = MembershipFactory()
        self._test_model_instance_serialization(membership, {
            'id': membership.id,
            'name': membership.name,
        })


class UserSerializerTestCase(SerializerTestCase):
    _serializer_class = UserSerializer

    @classmethod
    def setUpTestData(cls):
        cls._user = UserFactory()

    def setUp(self):
        self.__test_data = {
            'username': 'username'
        }

    def __get_test_data(self, password):
        self.__test_data['password'] = password

        return self.__test_data

    def __test_password_regex_validation(self, password):
        self._test_serializer_raise_validation_error('This value does not match the required pattern.', data=self.__get_test_data(password))

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
        self.__test_password_regex_validation('username00')

    def test_uppercase_number_password_regex_validation(self):
        self.__test_password_regex_validation('USERNAME00')

    def test_lowercase_uppercase_password_regex_validation(self):
        self.__test_password_regex_validation('usernameUSERNAME')

    def test_password_similarity_validation(self):
        self._test_serializer_raise_validation_error('The similarity between password and username is too large.', data=self.__get_test_data('Username00'))

    def test_update(self):
        original_password = get_factory_password(self._user)
        serializer = self._get_serializer_after_validation(instance=self._user, data=self.__test_data ,partial=True)
        self._user = serializer.save()

        self.assertEqual(self._user.username, self.__test_data['username'])
        self.assertTrue(self._user.check_password(original_password))
        self.assertEqual(self._user.created_at, self._user.last_update_password)


class ShopperSerializerTestCase(SerializerTestCase):
    _serializer_class = ShopperSerializer

    def test_model_instance_serialization(self):
        shopper = ShopperFactory()
        self._test_model_instance_serialization(shopper, {
            **UserSerializer(instance=shopper).data,
            'membership': MembershipSerializer(instance=shopper.membership).data,
            'name': shopper.name,
            'nickname': shopper.nickname,
            'mobile_number': shopper.mobile_number,
            'email': shopper.email,
            'gender': shopper.gender,
            'birthday': shopper.birthday,
            'height': shopper.height,
            'weight': shopper.weight,
            'point': shopper.point,
        })


class WholesalerSerializerTestCase(SerializerTestCase):
    _serializer_class = WholesalerSerializer

    def test_model_instance_serialization(self):
        wholesaler = WholesalerFactory()

        self._test_model_instance_serialization(wholesaler, {
            **UserSerializer(instance=wholesaler).data,
            'name': wholesaler.name,
            'mobile_number': wholesaler.mobile_number,
            'phone_number': wholesaler.phone_number,
            'email': wholesaler.email,
            'company_registration_number': wholesaler.company_registration_number,
            'business_registration_image_url': wholesaler.business_registration_image_url,
            'zip_code': wholesaler.zip_code,
            'base_address': wholesaler.base_address,
            'detail_address': wholesaler.detail_address,
            'is_approved': wholesaler.is_approved,
        })


class BuildingSerializerTestCase(SerializerTestCase):
    _serializer_class = BuildingSerializer

    def test_model_instance_serialization(self):
        building = BuildingWithFloorFactory()

        self._test_model_instance_serialization(building, {
            'name': building.name,
            'zip_code': building.zip_code,
            'base_address': building.base_address,
            'floors': [floor.name for floor in Floor.objects.all()]
        })


class UserPasswordSerializerTestCase(SerializerTestCase):
    _serializer_class = UserPasswordSerializer

    @classmethod
    def setUpTestData(cls):
        cls._user = UserFactory()

    def setUp(self):
        self.__test_data = {
            'current_password': get_factory_password(self._user),
            'new_password': self._user.username + '_New_Password',
        }

    def __get_test_data(self, current_password=None, new_password=None):
        if current_password is not None:
            self.__test_data['current_password'] = current_password
        if new_password is not None:
            self.__test_data['new_password'] = new_password

        return self.__test_data

    def test_current_password_validation(self):
        self._test_serializer_raise_validation_error('current password does not correct.', instance=self._user, data=self.__get_test_data(current_password='weird_password'))
        
    def test_same_new_password_validation(self):
        self._test_serializer_raise_validation_error('new password is same as the current password.', instance=self._user, data=self.__get_test_data(new_password=self.__test_data['current_password']))

    def test_update(self):
        test_tokens = []
        for _ in range(3):
            test_tokens.append(RefreshToken.for_user(self._user))
        RefreshToken.for_user(self._user).blacklist()
        OutstandingToken.objects.filter(jti=RefreshToken.for_user(self._user)['jti']).update(expires_at=datetime.now())
        RefreshToken.for_user(UserFactory())
        serializer = self._get_serializer_after_validation(instance=self._user, data=self.__test_data)
        serializer.save()

        self.assertTrue(self._user.check_password(self.__test_data['new_password']))
        self.assertEqual(len(OutstandingToken.objects.all()), 6)
        self.assertEqual(len(OutstandingToken.objects.filter(blacklistedtoken__isnull=False)), 4)
        self.assertEqual(len(OutstandingToken.objects.filter(jti__in=[token['jti'] for token in test_tokens], blacklistedtoken__isnull=False)), 3)


class ShopperShippingAddressSerializerTestCase(SerializerTestCase):
    _serializer_class = ShopperShippingAddressSerializer

    @classmethod
    def setUpTestData(cls):
        cls.shopper = ShopperFactory()
        cls.data = {
            'name': '회사', 
            'receiver_name': '홍길동',
            'receiver_mobile_number': '01011111111',
            'receiver_phone_number': '03199999999',
            'zip_code': '12345',
            'base_address': '서울시 광진구 능동로19길 47',
            'detail_address': '518호',
            'is_default': True
        }


    def test_model_instance_serialization(self):
        shipping_address = ShopperShippingAddressFactory()
        
        self._test_model_instance_serialization(shipping_address, {
            'id': shipping_address.id,
            'name': shipping_address.name,
            'receiver_name': shipping_address.receiver_name,
            'receiver_mobile_number': shipping_address.receiver_mobile_number,
            'receiver_phone_number': shipping_address.receiver_phone_number,
            'zip_code': shipping_address.zip_code,
            'base_address': shipping_address.base_address,
            'detail_address': shipping_address.detail_address,
            'is_default': shipping_address.is_default,
        })

    def test_create(self):
        serializer = self._get_serializer_after_validation(data=self.data, context={'shopper': self.shopper})
        shipping_address = serializer.save()

        self.assertEqual(shipping_address.name, self.data['name'])
        self.assertEqual(shipping_address.receiver_name, self.data['receiver_name'])
        self.assertEqual(shipping_address.receiver_mobile_number, self.data['receiver_mobile_number'])
        self.assertEqual(shipping_address.receiver_phone_number, self.data['receiver_phone_number'])
        self.assertEqual(shipping_address.zip_code, self.data['zip_code'])
        self.assertEqual(shipping_address.base_address, self.data['base_address'])
        self.assertEqual(shipping_address.detail_address, self.data['detail_address'])
        self.assertEqual(shipping_address.is_default, self.data['is_default'])
        self.assertEqual(shipping_address.shopper, self.shopper)

    def test_create_initial_shipping_address(self):
        self.shopper.addresses.all().delete()
        self.data['is_default'] = False
        serializer = self._get_serializer_after_validation(data=self.data, context={'shopper': self.shopper})
        shipping_address = serializer.save()

        self.assertTrue(shipping_address.is_default)

    def test_create_default_shipping_address(self):
        ShopperShippingAddressFactory(shopper=self.shopper, is_default=True)

        serializer = self._get_serializer_after_validation(data=self.data, context={'shopper': self.shopper})
        shipping_address = serializer.save()

        self.assertTrue(shipping_address.is_default)
        self.assertTrue(
            not self.shopper.addresses.exclude(
                    id=shipping_address.id
                ).filter(is_default=True).exists()
        )

    def test_update(self):
        shipping_address = ShopperShippingAddressFactory()
        data = {
            'name': shipping_address.name + '_update',
            'receiver_name': shipping_address.receiver_name + '_update',
            'is_default': not shipping_address.is_default,
        }
        serializer = self._get_serializer_after_validation(
            instance=shipping_address, data=data, partial=True, context={'shopper': self.shopper}
        )
        updated_shipping_address = serializer.save()

        self.assertEqual(updated_shipping_address.name, data['name'])
        self.assertEqual(updated_shipping_address.receiver_name, data['receiver_name'])
        self.assertEqual(updated_shipping_address.is_default, data['is_default'])

    def test_update_to_default_shipping_address(self):
        ShopperShippingAddressFactory(shopper=self.shopper, is_default=True)
        shipping_address = ShopperShippingAddressFactory(shopper=self.shopper)
        data = {'is_default': True}

        serializer = self._get_serializer_after_validation(
            instance=shipping_address, data=data, partial=True, context={'shopper': self.shopper}
        )        
        shipping_address = serializer.save()

        self.assertTrue(shipping_address.is_default)
        self.assertTrue(
            not self.shopper.addresses.exclude(
                    id=shipping_address.id
                ).filter(is_default=True).exists()
        )


class PointHistorySerializerTestCase(SerializerTestCase):
    _serializer_class = PointHistorySerializer

    # todo order test code 구현 이후에 작업