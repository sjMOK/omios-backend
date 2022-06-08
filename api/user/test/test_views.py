from datetime import date, timedelta

from django.forms import model_to_dict
from django.db.models import Sum, F, Case, When

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from freezegun import freeze_time

from common.test.test_cases import ViewTestCase, FREEZE_TIME
from common.utils import datetime_to_iso
from coupon.test.factories import CouponFactory, CouponClassificationFactory
from coupon.serializers import CouponSerializer
from product.test.factories import ProductFactory, ProductColorFactory, OptionFactory
from .factories import (
    MembershipFactory, get_factory_password, get_factory_authentication_data, 
    FloorFactory, BuildingFactory, ShopperShippingAddressFactory, PointHistoryFactory, CartFactory,
    ShopperCouponFactory,
)
from ..models import (
    BlacklistedToken, ShopperShippingAddress, Membership, User, Shopper, Wholesaler, Building, Cart,
)
from ..serializers import (
    IssuingTokenSerializer, RefreshingTokenSerializer, ShopperSerializer, WholesalerSerializer, CartSerializer,
    BuildingSerializer, ShopperShippingAddressSerializer, PointHistorySerializer, ShopperCouponSerializer,
)


class TokenViewTestCase(ViewTestCase):
    @classmethod
    def _issue_token(cls):
        cls._set_user()
        token_serializer = IssuingTokenSerializer(data=get_factory_authentication_data(cls._user))
        token_serializer.is_valid()
        cls._test_data = token_serializer.validated_data

    def _refresh_token(self):
        token_serializer = RefreshingTokenSerializer(data=self._test_data)
        token_serializer.is_valid()

    def _assert_token(self):
        self.assertTrue(AccessToken(self._response_data['access']))
        self.assertTrue(RefreshToken(self._response_data['refresh']))
    
    def _assert_failure(self, expected_message):
        super()._assert_failure(401, expected_message)


class IssuingTokenViewTestCase(TokenViewTestCase):
    _url = '/users/tokens'

    @classmethod
    def setUpTestData(cls):
        cls._set_user()

    def setUp(self):
        self._test_data = get_factory_authentication_data(self._user)

    def test_success(self):
        self._post()
    
        self._assert_success()
        self._assert_token()
        
    def test_wrong_password(self):
        self._test_data['password'] = 'wrong_password'
        self._post()

        self._assert_failure('No active account found with the given credentials')

    def test_non_existent_user(self):
        self._test_data['username'] = 'non_existent_user'
        self._post()

        self._assert_failure('No active account found with the given credentials')
        

class RefreshingTokenViewTestCase(TokenViewTestCase):
    _url = '/users/tokens/refresh'

    @classmethod
    def setUpTestData(cls):
        cls._issue_token()

    def test_success(self):
        self._post()

        self._assert_success()
        self._assert_token()

    def test_failure_using_blacklisted_token(self):
        self._refresh_token()
        self._post()

        self._assert_failure('Token is blacklisted')

    def test_failure_using_abnormal_token(self):
        self._test_data = {'refresh': 'abnormal_token'}
        self._post()

        self._assert_failure('Token is invalid or expired')


class BlacklistingTokenViewTestCase(TokenViewTestCase):
    _url = '/users/tokens/blacklist'

    @classmethod
    def setUpTestData(cls):
        cls._issue_token()

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._test_data['access'])

    def test_success(self):
        self._post()

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], self._user.id)
        self.assertEqual(BlacklistedToken.objects.get(token__token=self._test_data['refresh']).token.user_id, self._user.id)


class ShopperViewSetTestCase(ViewTestCase):
    fixtures = ['coupon_classification', 'coupon']
    _url = '/users/shoppers'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()

    def setUp(self):
        self._set_authentication()

    def test_retrieve(self):
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, ShopperSerializer(instance=self._user).data)

    def test_create(self):
        self._unset_authentication()
        self._test_data = {
            "name": "테스트",
            "birthday": "2021-11-20",
            "gender": 1,
            "email": "test@naver.com",
            "mobile_number": "01011111111",
            "username": "xptmxm",
            "password": "Testtest00"
        }
        if not Membership.objects.filter(id=1).exists():
            MembershipFactory(id=1)
        self._post()
        user = Shopper.objects.get(username=self._test_data['username'])

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertTrue(user.check_password(self._test_data['password']))

    def test_partial_update(self):
        self._test_data = {
            'email': 'user@omios.com',
            'nickname': 'patch_test',
            'height': '180',
            'weight': 70
        }
        self._patch()
        user = Shopper.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertEqual(user.email, self._test_data['email'])
        self.assertEqual(user.nickname, self._test_data['nickname'])
        self.assertEqual(user.height, int(self._test_data['height']))
        self.assertEqual(user.weight, self._test_data['weight'])

    def test_partial_update_with_non_existent_field(self):
        self._test_data = {
            'email': 'user@omios.com',
            'non_existent_field': 'test',
        }
        self._patch()

        self._assert_failure(400, 'It contains requests for fields that do not exist or cannot be modified.')

    def test_partial_update_with_non_modifiable_field(self):
        self._test_data = {
            'nickname': 'patch_error_test',
            'password': 'test',
        }
        self._patch()

        self._assert_failure(400, 'It contains requests for fields that do not exist or cannot be modified.')

    @freeze_time(FREEZE_TIME)
    def test_destroy(self):
        self._delete()
        user = Shopper.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertTrue(not user.is_active)
        self.assertEqual(datetime_to_iso(user.deleted_at), FREEZE_TIME)


class WholesalerViewSetTestCase(ViewTestCase):
    _url = '/users/wholesalers'

    @classmethod
    def setUpTestData(cls):
        cls._set_wholesaler()

    def setUp(self):
        self._set_authentication()

    def test_retrieve(self):
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, WholesalerSerializer(instance=self._user).data)

    def test_create(self):
        self._unset_authentication()
        self._test_data = {
            "username": "pippin",
            "password": "Ahrtmdwn123",
            "name": "피핀",
            "mobile_number": "01099887766",
            "phone_number": "0299887711",
            "email": "pippin@naver.com",
            "company_registration_number": "2921300894",
            "business_registration_image_url": "https://deepy.s3.ap-northeast-2.amazonaws.com/media/business_registration/business_registration_20220305_145614222569.jpeg",
            "zip_code": "04568",
            "base_address": "서울특별시 중구 다산로 293 (신당동, 디오트)",
            "detail_address": "디오트 1층 102호"
        }
        self._post()
        user = Wholesaler.objects.get(username=self._test_data['username'])

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertTrue(user.check_password(self._test_data['password']))

    def test_partial_update(self):
        self._test_data = {
            'mobile_number': '01000000000',
            'email': 'user@omios.com'
        }
        self._patch()
        user = Wholesaler.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertEqual(user.mobile_number, self._test_data['mobile_number'])
        self.assertEqual(user.email, self._test_data['email'])

    @freeze_time(FREEZE_TIME)
    def test_destroy(self):
        self._delete()
        user = Wholesaler.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertTrue(not user.is_active)
        self.assertEqual(datetime_to_iso(user.deleted_at), FREEZE_TIME)


class UploadBusinessRegistrationImageTestCase(ViewTestCase):
    _url = '/users/wholesalers/business_registration_images'

    def test_success(self):
       self._test_image_upload(middle_path='/business_registration/business_registration_')


class GetBuildingTestCase(ViewTestCase):
    _url = '/users/wholesalers/buildings'

    def test_success(self):
        floors = FloorFactory.create_batch(3)
        BuildingFactory(floors=floors)
        BuildingFactory(floors=floors[0:2])
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data, BuildingSerializer(instance=Building.objects.all(), many=True).data)


class ChangePasswordTestCase(ViewTestCase):
    _url = '/users/passwords'

    @classmethod
    def setUpTestData(cls):
        cls._set_user()

    @freeze_time(FREEZE_TIME)
    def test_success(self):
        self._set_authentication()
        self._test_data = {
            'current_password': get_factory_password(self._user),
            'new_password': 'New_password00'
        }
        self._patch()
        self._user = User.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], self._user.id)
        self.assertTrue(self._user.check_password(self._test_data['new_password']))
        self.assertEqual(datetime_to_iso(self._user.last_update_password), FREEZE_TIME)


class IsUniqueTestCase(ViewTestCase):
    _url = '/users/unique'

    @classmethod
    def setUpTestData(cls):
        cls.__shopper = cls._create_shopper()[0]
        cls.__wholesaler = cls._create_wholesaler()[0]

    def test_is_unique_username(self):
        self._get({'username': 'unique_username'})

        self._assert_success_with_is_unique_response(True)

    def test_is_not_unique_username(self):
        self._get({'username': self.__shopper.username})

        self._assert_success_with_is_unique_response(False)

    def test_is_unique_shopper_nickname(self):
        self._get({'shopper_nickname': 'unique_nickname'})

        self._assert_success_with_is_unique_response(True)

    def test_is_not_unique_shopper_nickname(self):
        self._get({'shopper_nickname': self.__shopper.nickname})

        self._assert_success_with_is_unique_response(False)

    def test_is_unique_wholesaler_name(self):
        self._get({'wholesaler_name': 'unique_name'})

        self._assert_success_with_is_unique_response(True)

    def test_is_not_unique_wholesaler_name(self):
        self._get({'wholesaler_name': self.__wholesaler.name})

        self._assert_success_with_is_unique_response(False)

    def test_is_unique_wholesaler_company_registration_number(self):
        self._get({'wholesaler_company_registration_number': '012345678901'})

        self._assert_success_with_is_unique_response(True)

    def test_is_not_unique_wholesaler_company_registration_number(self):
        self._get({'wholesaler_company_registration_number': self.__wholesaler.company_registration_number})

        self._assert_success_with_is_unique_response(False)

    def test_no_parameter_validation(self):
        self._get()

        self._assert_failure(400, 'Only one parameter is allowed.')

    def test_many_paramter_validation(self):
        self._get({'parameter1': 'parameter1', 'parameter2': 'parameter2'})

        self._assert_failure(400, 'Only one parameter is allowed.')

    def test_invalid_parameter_validation(self):
        self._get({'invalid_parameter': 'test'})

        self._assert_failure(400, 'Invalid parameter name.')


class ProductLikeViewTestCase(ViewTestCase):
    _url = '/users/shoppers/like/products/{}'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__product = ProductFactory()
        cls._url = cls._url.format(cls.__product.id)
        cls._test_data = {'product_id': cls.__product.id}

    def test_post(self):
        self._set_authentication()
        self._post()

        self._assert_success()
        self.assertEqual(self._response_data['shopper_id'], self._user.id)
        self.assertEqual(self._response_data['product_id'], self.__product.id)

    def test_delete(self):
        self._user.like_products.add(self.__product)
        self._set_authentication()
        self._delete()

        self._assert_success()
        self.assertEqual(self._response_data['shopper_id'], self._user.id)
        self.assertEqual(self._response_data['product_id'], self.__product.id)

    def test_post_duplicated_like(self):
        self._user.like_products.add(self.__product)
        self._set_authentication()
        self._post()

        self._assert_failure(400, 'Duplicated user and product')
    
    def test_delete_non_eixist_like(self):
        self._set_authentication()
        self._delete()

        self._assert_failure(400, 'You are deleting non exist likes')


class CartViewSetTestCase(ViewTestCase):
    _url = '/users/shoppers/carts'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__product_color = ProductColorFactory()
        cls.__carts = CartFactory.create_batch(2, option__product_color=cls.__product_color)
        cls._user.carts.add(*cls.__carts)

    def setUp(self):
        self._set_authentication()

    def test_list(self):
        queryset = self._user.carts.all()
        aggregate_data = queryset.aggregate(
            total_sale_price=Sum(F('option__product_color__product__sale_price') * F('count')),
            total_base_discounted_price=Sum(F('option__product_color__product__base_discounted_price') * F('count'))
        )
        serializer = CartSerializer(queryset, many=True)
        self._get()

        self.assertListEqual(self._response_data['results'], serializer.data)
        self.assertEqual(self._response_data['total_sale_price'], aggregate_data['total_sale_price'])
        self.assertEqual(self._response_data['total_base_discounted_price'], aggregate_data['total_base_discounted_price'])

    def test_create(self):
        self._test_data = [{
            'option': OptionFactory(product_color=self.__product_color).id,
            'count': 1,
        },
        {
            'option': OptionFactory(product_color=self.__product_color).id,
            'count': 1,
        }]
        self._post(format='json')

        self._assert_success_and_serializer_class(CartSerializer, False)

    def test_partial_update(self):
        updating_cart = self.__carts[0]
        self._test_data = {
            'count': updating_cart.count + 1,
        }
        self._url += '/{}'.format(updating_cart.id)
        self._patch()
        updated_cart = Cart.objects.get(id=self._response_data['id'])

        self._assert_success_with_id_response()
        self.assertEqual(updated_cart.count, self._test_data['count'])

    def test_partial_update_with_unpatchable_fields(self):
        updating_cart = self.__carts[0]
        self._test_data = {
            'id': updating_cart.id,
            'count': updating_cart.count,
        }
        self._url += '/{}'.format(updating_cart.id)
        self._patch()

        self._assert_failure_for_non_patchable_field()

    def test_remove(self):
        self._test_data = {
            'id': [cart.id for cart in self.__carts],
        }
        self._url += '/remove'
        self._post(status_code=200, format='json')

        self._assert_success()
        self.assertTrue(not self._user.carts.filter(id__in=self._response_data['id']))

    def test_remove_without_id_list(self):
        self._test_data = {}
        self._url += '/remove'
        self._post(format='json')

        self._assert_failure(400, 'list of id is required.')

    def test_remove_with_non_integer_values_list(self):
        self._test_data = {
            'id': [str(cart.id) for cart in self.__carts],
        }
        self._url += '/remove'
        self._post(format='json')

        self._assert_failure(400, 'values in the list must be integers.')

    def test_remove_with_non_list_id(self):
        self._test_data = {
            'id': self.__carts[0].id
        }
        self._url += '/remove'
        self._post(format='json')

        self._assert_failure(400, 'values in the list must be integers.')

    def test_remove_raise_permission_denied(self):
        cart = CartFactory(option__product_color=self.__product_color)
        self._test_data = {
            'id': [self.__carts[0].id, cart.id]
        }
        self._url += '/remove'
        self._post(format='json')
        
        self._assert_failure(403, 'You do not have permission to perform this action.')


class ShopperShippingAddressViewSetTestCase(ViewTestCase):
    _url = '/users/shoppers/addresses'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__default_shipping_address = ShopperShippingAddressFactory(shopper=cls._user, is_default=True)
        ShopperShippingAddressFactory.create_batch(size=2, shopper=cls._user)

    def __get_queryset(self):
        order_condition = [Case(When(is_default=True, then=1), default=2), '-id']
        queryset = self._user.addresses.all().order_by(*order_condition)

        return queryset

    def test_list(self):
        queryset = self.__get_queryset()
        serializer = ShopperShippingAddressSerializer(queryset, many=True)

        self._set_authentication()
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data, serializer.data)

    def test_create(self):
        self._test_data = {
            'name': '회사', 
            'receiver_name': '홍길동',
            'receiver_mobile_number': '01011111111',
            'receiver_phone_number': '03199999999',
            'zip_code': '12345',
            'base_address': '서울시 광진구 능동로19길 47',
            'detail_address': '518호',
            'is_default': True
        }
        self._set_authentication()
        self._post()

        self._assert_success_with_id_response()

        shipping_address = ShopperShippingAddress.objects.get(id=self._response_data['id'])
        self.assertDictEqual(
            model_to_dict(shipping_address, fields=self._test_data.keys()),
            self._test_data
        )

    def test_partial_update(self):
        shipping_address = self.__default_shipping_address
        self._test_data = {
            'name': shipping_address.name + '_update',
            'receiver_name': shipping_address.receiver_name + '_update',
            'is_default': not shipping_address.is_default,
        }
        self._set_authentication()
        self._url = self._url + '/{0}'.format(shipping_address.id)
        self._patch()

        self._assert_success_with_id_response()

        shipping_address = ShopperShippingAddress.objects.get(id=self._response_data['id'])
        self.assertDictEqual(
            model_to_dict(shipping_address, fields=self._test_data.keys()),
            self._test_data
        )

    def test_destroy(self):
        shipping_address = self.__default_shipping_address
        self._set_authentication()
        self._url = self._url + '/{0}'.format(shipping_address.id)
        self._delete()

        self._assert_success_with_id_response()
        self.assertTrue(not ShopperShippingAddress.objects.filter(id=shipping_address.id).exists())

    def test_get_default_address(self):
        self._set_authentication()
        self._url += '/default'
        self._get()
        serializer = ShopperShippingAddressSerializer(self.__default_shipping_address)

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)

    def test_get_default_address_with_no_default_address(self):
        self.__default_shipping_address.is_default = False
        self.__default_shipping_address.save()

        self._set_authentication()
        self._url += '/default'
        self._get()

        queryset = self.__get_queryset()
        serializer = ShopperShippingAddressSerializer(
            queryset.first()
        )

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)

    def test_get_default_address_with_mutiple_default_address(self):
        shipping_address = ShopperShippingAddress.objects.filter(is_default=False).last()
        shipping_address.is_default = True
        shipping_address.save()

        self._set_authentication()
        self._url += '/default'
        self._get()
        serializer = ShopperShippingAddressSerializer(
            ShopperShippingAddress.objects.filter(is_default=True).last()
        )

        self._assert_success()
        self.assertDictEqual(self._response_data, serializer.data)

    def test_get_default_address_return_empty_dictionary(self):
        self._user.addresses.all().delete()
        self._set_authentication()
        self._url += '/default'
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, {})


class GetPointHistoriesTestCase(ViewTestCase):
    _url = '/users/shoppers/point-histories'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()

    def test_success(self):
        self._set_authentication()
        PointHistoryFactory.create_batch(2, shopper=self._user)
        self._get()
        
        self._assert_success()
        self.assertListEqual(self._response_data, PointHistorySerializer(self._user.point_histories.all(), many=True).data)


class ShopperCouponViewSetTestCase(ViewTestCase):
    _url = '/users/shoppers/coupons'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        cls.__coupon_classification = CouponClassificationFactory()
        coupons = CouponFactory.create_batch(2, classification=cls.__coupon_classification)
        for coupon in coupons:
            ShopperCouponFactory(shopper=cls._user, coupon=coupon, is_available=True)

    def setUp(self):
        self._set_authentication()

    def test_list(self):
        queryset = self._user.coupons.all().order_by('-shoppercoupon__coupon')
        serializer = CouponSerializer(queryset, many=True)
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], serializer.data)

    def test_list_with_not_available_coupon(self):
        queryset = self._user.coupons.all().order_by('-shoppercoupon__coupon')
        serializer = CouponSerializer(queryset, many=True)
        expected_data = serializer.data

        coupon = CouponFactory(classification=self.__coupon_classification)
        ShopperCouponFactory(shopper=self._user, coupon=coupon, is_available=False)
        
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], expected_data)

    def test_list_with_expired_coupont(self):
        queryset = self._user.coupons.all().order_by('-shoppercoupon__coupon')
        serializer = CouponSerializer(queryset, many=True)
        expected_data = serializer.data

        coupon = CouponFactory(classification=self.__coupon_classification)
        ShopperCouponFactory(shopper=self._user, coupon=coupon, end_date=date.today() - timedelta(days=1))
        
        self._get()

        self._assert_success()
        self.assertListEqual(self._response_data['results'], expected_data)

    def test_create(self):
        coupon = CouponFactory(classification=self.__coupon_classification, is_auto_issue=False)
        self._test_data = {
            'coupon': coupon.id,
        }
        self._post()

        self._assert_success_and_serializer_class(ShopperCouponSerializer, False)
        self.assertEqual(self._response_data, {'coupon_id': str(coupon.id)})
