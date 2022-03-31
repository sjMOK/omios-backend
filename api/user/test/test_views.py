from freezegun import freeze_time
from django.test import tag
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.test.test_cases import ViewTestCase, FREEZE_TIME
from common.utils import datetime_to_iso
from .factory import get_factory_password, get_factory_authentication_data, FloorFactory, BuildingFactory
from ..models import BlacklistedToken, User, Shopper, Wholesaler, Building
from ..serializers import IssuingTokenSerializer, RefreshingTokenSerializer, ShopperSerializer, WholesalerSerializer, BuildingSerializer


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
    fixtures = ['membership']
    _url = '/users/shoppers'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()

    def setUp(self):
        self._set_authentication()

    def test_retrieve(self):
        self._url += '/{0}'.format(self._user.id)
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
        self._post()
        user = Shopper.objects.get(username=self._test_data['username'])

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], user.id)
        self.assertTrue(user.check_password(self._test_data['password']))

    def test_partial_update(self):
        self._url += '/{0}'.format(self._user.id)
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
        self._url += '/{0}'.format(self._user.id)
        self._test_data = {
            'email': 'user@omios.com',
            'non_existent_field': 'test',
        }
        self._patch()

        self._assert_failure(400, 'It contains requests for fields that do not exist or cannot be modified.')

    def test_partial_update_with_non_modifiable_field(self):
        self._url += '/{0}'.format(self._user.id)
        self._test_data = {
            'nickname': 'patch_error_test',
            'password': 'test',
        }
        self._patch()

        self._assert_failure(400, 'It contains requests for fields that do not exist or cannot be modified.')

    @freeze_time(FREEZE_TIME)
    def test_destroy(self):
        self._url += '/{0}'.format(self._user.id)
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
        self._url += '/{0}'.format(self._user.id)
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
        self._url += '/{0}'.format(self._user.id)
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
        self._url += '/{0}'.format(self._user.id)
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

    def test_sucess(self):
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
    fixtures = ['membership']
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
