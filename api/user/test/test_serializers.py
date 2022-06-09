from datetime import datetime, timedelta, date
from decimal import Decimal

from rest_framework.exceptions import ValidationError

from common.test.test_cases import FunctionTestCase, SerializerTestCase, ListSerializerTestCase
from common.utils import gmt_to_kst, datetime_to_iso, BASE_IMAGE_URL, DEFAULT_IMAGE_URL
from coupon.test.factories import CouponFactory, CouponClassificationFactory
from coupon.models import CouponClassification, Coupon
from order.serializers import ORDER_MAXIMUM_NUMBER
from product.test.factories import ProductFactory, ProductImageFactory, ProductColorFactory, OptionFactory
from .factories import (
    get_factory_password, get_factory_authentication_data, 
    MembershipFactory, UserFactory, ShopperFactory, WholesalerFactory, CartFactory, BuildingWithFloorFactory,
    ShopperShippingAddressFactory, PointHistoryFactory, ShopperCouponFactory,
)
from ..models import OutstandingToken, Floor
from ..serializers import (
    get_token_time,
    IssuingTokenSerializer, RefreshingTokenSerializer, RefreshToken, MembershipSerializer, 
    UserSerializer, ShopperSerializer, WholesalerSerializer, CartSerializer, BuildingSerializer, UserPasswordSerializer,
    ShopperShippingAddressSerializer, PointHistorySerializer, ShopperCouponSerializer,
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
            'discount_rate': str(membership.discount_rate),
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
    fixtures = ['coupon_classification', 'coupon']
    _serializer_class = ShopperSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__membership = MembershipFactory(id=1)

    def test_model_instance_serialization(self):
        shopper = ShopperFactory(membership=self.__membership)
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

    def test_add_signup_coupons(self):
        shopper = ShopperFactory.build(membership=self.__membership)
        self._test_data = {
            'username': shopper.username,
            'name': shopper.name,
            'mobile_number': shopper.mobile_number,
            'email': shopper.email,
            'gender': shopper.gender,
            'birthday': shopper.birthday,
            'height': shopper.height,
            'weight': shopper.weight,
            'password': shopper.password,
        }
        serializer = self._get_serializer_after_validation()
        shopper = serializer.save()
        signup_coupons = Coupon.objects.filter(classification_id=5)

        self.assertQuerysetEqual(shopper.coupons.all(), signup_coupons, ordered=False)


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


class CartListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = CartSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__shopper = ShopperFactory()

        cls.__product_1 = ProductFactory()
        cls.__product_color_1 = ProductColorFactory(product=cls.__product_1)
        ProductImageFactory(product=cls.__product_1)

        cls.__product_2 = ProductFactory(product=cls.__product_1)
        cls.__product_color_2 = ProductColorFactory(product=cls.__product_2)
        ProductImageFactory(product=cls.__product_2)

        CartFactory.create_batch(2, option__product_color=cls.__product_color_1, shopper=cls.__shopper)
        CartFactory.create_batch(2, option__product_color=cls.__product_color_2, shopper=cls.__shopper)

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

    def test_validate_count_of_carts(self):
        product_color = ProductColorFactory(product=self.__product_1)
        data = [{'option': OptionFactory(product_color=product_color).id, 'count': 1} for _ in range(ORDER_MAXIMUM_NUMBER)]

        self._test_serializer_raise_validation_error(
            'exceeded'.format(ORDER_MAXIMUM_NUMBER),
            data=data, context={'shopper': self.__shopper}
        )

    def test_create(self):
        data = [{
            'option': OptionFactory(product_color=self.__product_color_1).id,
            'count': 1,
        }]
        serializer = self._get_serializer_after_validation(data=data, context={'shopper': self.__shopper})
        serializer.save()
        cart = self.__shopper.carts.get(option_id=data[0]['option'])

        self.assertEqual(cart.option.id, data[0]['option']),
        self.assertEqual(cart.shopper, self.__shopper)
        self.assertEqual(cart.count, data[0]['count'])

    def test_create_option_already_exists(self):
        cart = self.__shopper.carts.first()
        data = [{
            'option': cart.option.id,
            'count': 1
        }]
        serializer = self._get_serializer_after_validation(data=data, context={'shopper': self.__shopper})
        serializer.save()
        updated_cart = self.__shopper.carts.get(option_id=data[0]['option'])

        self.assertEqual(updated_cart, cart)
        self.assertEqual(updated_cart.count, cart.count + data[0]['count'])


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


class ShopperCouponSerializerTestCase(SerializerTestCase):
    _serializer_class = ShopperCouponSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__shopper = ShopperFactory()
        cls.__coupon_classification = CouponClassificationFactory()
        cls.__coupon = CouponFactory(is_auto_issue=False, classification=cls.__coupon_classification)

    def test_create_end_date_coupon(self):
        self._test_data = {
            'coupon': self.__coupon.id
        }
        serializer = self._get_serializer_after_validation()
        shopper_coupon = serializer.save(shopper=self.__shopper)

        self.assertEqual(shopper_coupon.shopper, self.__shopper)
        self.assertEqual(shopper_coupon.coupon, self.__coupon)
        self.assertEqual(shopper_coupon.end_date, self.__coupon.end_date)
        self.assertEqual(shopper_coupon.is_available, True)

    def test_create_available_period_coupon(self):
        coupon = CouponFactory(is_auto_issue=False, start_date=None, end_date=None, available_period=7, classification=self.__coupon_classification)
        self._test_data = {
            'coupon': coupon.id
        }
        serializer = self._get_serializer_after_validation()
        shopper_coupon = serializer.save(shopper=self.__shopper)

        self.assertEqual(shopper_coupon.shopper, self.__shopper)
        self.assertEqual(shopper_coupon.coupon, coupon)
        self.assertEqual(shopper_coupon.end_date, date.today() + timedelta(days=coupon.available_period))
        self.assertEqual(shopper_coupon.is_available, True)

    def test_create_already_existing_coupon(self):
        ShopperCouponFactory(shopper=self.__shopper, coupon=self.__coupon)
        self._test_data = {
            'coupon': self.__coupon.id
        }
        serializer = self._get_serializer_after_validation()

        self.assertRaisesMessage(
            ValidationError,
            'already exists.',
            serializer.save,
            shopper=self.__shopper
        )

    def test_create_auto_issued_coupon(self):
        coupon = CouponFactory(is_auto_issue=True, classification=self.__coupon_classification)
        self._test_data = {
            'coupon': coupon.id
        }
        
        self._test_serializer_raise_validation_error(
            'object does not exist.',
            self._get_serializer_after_validation,
        )

    def test_create_expired_coupon(self):
        coupon = CouponFactory(end_date=date.today() - timedelta(days=1), classification=self.__coupon_classification)
        self._test_data = {
            'coupon': coupon.id
        }
        
        self._test_serializer_raise_validation_error(
            'object does not exist.',
            self._get_serializer_after_validation,
        )
