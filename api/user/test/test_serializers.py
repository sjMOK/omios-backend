from datetime import datetime

from common.test.test_cases import FunctionTestCase, SerializerTestCase, ListSerializerTestCase
from common.utils import gmt_to_kst, datetime_to_iso, BASE_IMAGE_URL, DEFAULT_IMAGE_URL
from order.serializers import ORDER_MAXIMUM_NUMBER
from product.test.factories import ProductFactory, ProductImageFactory, ProductColorFactory, OptionFactory
from .factories import (
    get_factory_password, get_factory_authentication_data, 
    MembershipFactory, UserFactory, ShopperFactory, WholesalerFactory, CartFactory, BuildingWithFloorFactory,
    ShopperShippingAddressFactory, PointHistoryFactory,
)
from ..models import OutstandingToken, Floor
from ..serializers import (
    get_token_time,
    IssuingTokenSerializer, RefreshingTokenSerializer, RefreshToken, MembershipSerializer, 
    UserSerializer, ShopperSerializer, WholesalerSerializer, CartSerializer, BuildingSerializer, UserPasswordSerializer,
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
            'discount_rate': float(membership.discount_rate),
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


class CartSerializerTestCase(SerializerTestCase):
    _serializer_class = CartSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__product = ProductFactory()
        cls.__product_color = ProductColorFactory(product=cls.__product)
        ProductImageFactory.create_batch(size=3, product=cls.__product)
        cls.__shopper = ShopperFactory()
        cls.__cart = CartFactory(option__product_color=cls.__product_color, shopper=cls.__shopper)

    def test_model_instance_serialization(self):
        self._test_model_instance_serialization(self.__cart, {
            'id': self.__cart.id,
            'display_color_name': self.__cart.option.product_color.display_color_name,
            'size': self.__cart.option.size,
            'count': self.__cart.count,
            'option': self.__cart.option.id,
            'product_id': self.__cart.option.product_color.product.id,
            'product_name': self.__cart.option.product_color.product.name,
            'image': BASE_IMAGE_URL + self.__cart.option.product_color.product.images.all()[0].image_url,
            'base_discounted_price': self.__cart.option.product_color.product.base_discounted_price * self.__cart.count,
        })

    def test_model_instance_serialization_default_image_url(self):
        product = ProductFactory(product=self.__product)
        cart = CartFactory(option__product_color__product=product)

        self._test_model_instance_serialization(cart, {
            'id': cart.id,
            'display_color_name': cart.option.product_color.display_color_name,
            'size': cart.option.size,
            'count': cart.count,
            'option': cart.option.id,
            'product_id': cart.option.product_color.product.id,
            'product_name': cart.option.product_color.product.name,
            'image': DEFAULT_IMAGE_URL,
            'base_discounted_price': cart.option.product_color.product.base_discounted_price * cart.count,
        })

    def test_validate_count_of_carts(self):   
        product_color = ProductColorFactory(product=self.__product)
        for _ in range(ORDER_MAXIMUM_NUMBER):
            CartFactory(shopper=self.__shopper, option=OptionFactory(product_color=product_color))
        data = {
            'option': OptionFactory(product_color=product_color).id,
            'count': 1,
        }

        self._test_serializer_raise_validation_error(
            'exceeded the maximum number({}).'.format(ORDER_MAXIMUM_NUMBER),
            data=data, context={'shopper': self.__shopper}
        )

    def test_create(self):
        data = {
            'option': OptionFactory(product_color=self.__product_color).id,
            'count': 1,
        }
        serializer = self._get_serializer_after_validation(data=data, context={'shopper': self.__shopper})
        cart = serializer.save()

        self.assertEqual(cart.option.id, data['option']),
        self.assertEqual(cart.shopper, self.__shopper)
        self.assertEqual(cart.count, data['count'])

    def test_create_option_already_exists(self):
        data = {
            'option': self.__cart.option.id,
            'count': 1
        }
        serializer = self._get_serializer_after_validation(data=data, context={'shopper': self.__shopper})
        cart = serializer.save()

        self.assertEqual(cart, self.__cart)
        self.assertEqual(cart.count, self.__cart.count + data['count'])


class CartListSerializerTestCase(ListSerializerTestCase):
    maxDiff = None
    _child_serializer_class = CartSerializer

    def setUp(self):
        self.__shopper = ShopperFactory()

        self.__product_1 = ProductFactory()
        product_color_1 = ProductColorFactory(product=self.__product_1)
        ProductImageFactory(product=self.__product_1)

        self.__product_2 = ProductFactory(product=self.__product_1)
        product_color_2 = ProductColorFactory(product=self.__product_2)
        ProductImageFactory(product=self.__product_2)

        CartFactory.create_batch(2, option__product_color=product_color_1, shopper=self.__shopper)
        CartFactory.create_batch(2, option__product_color=product_color_2, shopper=self.__shopper)

    def test_to_representation(self):
        serializer = self._get_serializer(self.__shopper.carts.all())
        products = [self.__product_2, self.__product_1]
        
        expected_data = [
            {
                'product_id': product.id,
                'product_name': product.name,
                'image': BASE_IMAGE_URL + product.images.all()[0].image_url,
                'carts': [
                    {
                        'id': cart.id,
                        'base_discounted_price': cart.option.product_color.product.base_discounted_price * cart.count,
                        'display_color_name': cart.option.product_color.display_color_name,
                        'size': cart.option.size,
                        'count': cart.count,
                        'option': cart.option.id,
                    } for cart in self.__shopper.carts.filter(option__product_color__product=product)
                ],
            } for product in products
        ]

        self.assertListEqual(expected_data, serializer.data)


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


class PointHistorySerializerTestCase(SerializerTestCase):
    _serializer_class = PointHistorySerializer

    def test_model_instance_serialization(self):
        point_history = PointHistoryFactory()

        self._test_model_instance_serialization(point_history, {
            'id': point_history.id,
            'order_number': point_history.order.number,
            'product_name': point_history.product_name,
            'point': point_history.point,
            'content': point_history.content,
            'created_at': datetime_to_iso(point_history.created_at),
        })
