from gc import freeze
import json
from rest_framework.test import APITestCase, APITransactionTestCase
from freezegun import freeze_time
from django.test import tag

from common.test import ViewTestCase, FREEZE_TIME
from common.factory import get_factory_authentication_data, UserFactory
from common.utils import datetime_to_iso
from ..models import BlacklistedToken, Shopper
from ..serializers import IssuingTokenSerializer, RefreshingTokenSerializer, ShopperSerializer, WholesalerSerializer

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from pdb import set_trace


# class ShopperViewTestCase(DefaultViewTestCase):
#     fixtures = ['membership']

#     def test_bad_request_post(self):
#         request_body = {
#             "name": "테스트test",
#             "birthday": "20211120",
#             "gender": 2,
#             "email": "1235asdfasdf",
#             "phone": "0101111111212123",
#             "username": "tt",
#             "password": "testtest"
#         }

#         response = self.client.post('/user/shopper/', request_body)
#         response_body = json.loads(response.content)

#         self._assert_error(response_body, 400)
#         for key in request_body.keys():
#             self.assertTrue(key in response_body['message'])
    
#     def test_success_post(self):
#         request_body = {
#             "name": "테스트",
#             "birthday": "2021-11-20",
#             "gender": 1,
#             "email": "test@naver.com",
#             "phone": "01011111111",
#             "username": "xptmxm",
#             "password": "Testtest00"
#         }

#         response = self.client.post('/user/shopper/', request_body)
#         response_body = json.loads(response.content)
       
#         self._assert_success(response_body, 201)
#         self.assertTrue('id' in response_body['data'])
        

# @tag('aa')
# class UniqueViewTestCase(APITestCase):
#     _test_url = '/user/unique/'

#     def test_parameter_count_validation(self):
#         test_datas = [
#             None,
#             {
#                 'parameter1': '1',
#                 'parameter2': '2',
#             }
#         ]

#         for test_data in test_datas:
#             response = self.client.get(self._test_url)
#             response_body = json.loads(response.content)

            # self.assert

    # def test_parameter_name_validation(self):
    #     pass

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
        # self.assertEqual(self._response_body['message'], message)    


class IssuingTokenViewTestCase(TokenViewTestCase):
    _url = '/token/'

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
    _url = '/token/refresh/'

    @classmethod
    def setUpTestData(cls):
        cls._issue_token()

    # def setUp(self):
    #     self._test_data = self._token

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
    _url = '/token/blacklist/'        

    @classmethod
    def setUpTestData(cls):
        cls._issue_token()

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self._test_data['access'])
        # self._set_jwt()
        # self._test_data = self._token

    def test_success(self):
        self._post()

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], self._user.id)
        self.assertEqual(BlacklistedToken.objects.get(token__token=self._test_data['refresh']).token.user_id, self._user.id)


class ShopperViewTestCase(ViewTestCase):
    fixtures = ['membership']
    _url = '/user/shopper/'

    @classmethod
    def setUpTestData(cls):
        cls._set_shopper()
        # token_serializer = IssuingTokenSerializer(data=get_factory_authentication_data(cls._user))
        # token_serializer.is_valid()
        # cls._token = token_serializer.validated_data

    def setUp(self):
        self._set_authentication()

    def test_get(self):
        self._get()

        self._assert_success()
        self.assertDictEqual(self._response_data, ShopperSerializer(instance=self._user).data)

    def test_post(self):
        self._unset_authentication()
        self._test_data = {
            "name": "테스트",
            "birthday": "2021-11-20",
            "gender": 1,
            "email": "test@naver.com",
            "phone": "01011111111",
            "username": "xptmxm",
            "password": "Testtest00"
        }
        self._post()
        self._user = Shopper.objects.get(username=self._test_data['username'])

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], self._user.id)
        self.assertTrue(self._user.check_password(self._test_data['password']))

    def test_patch(self):
        self._test_data = {
            'email': 'user@omios.com',
            'nickname': 'patch_test',
            'height': '180',
            'weight': 70
        }
        self._patch()
        self._user = Shopper.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], self._user.id)
        self.assertEqual(self._user.email, self._test_data['email'])
        self.assertEqual(self._user.nickname, self._test_data['nickname'])
        self.assertEqual(self._user.height, int(self._test_data['height']))
        self.assertEqual(self._user.weight, self._test_data['weight'])

    def test_patch_with_non_existent_field(self):
        self._test_data = {
            'email': 'user@omios.com',
            'non_existent_field': 'test',
        }
        self._patch()

        self._assert_failure(400, 'It contains requests for fields that do not exist or cannot be modified.')

    def test_patch_with_non_modifiable_field(self):
        self._test_data = {
            'nickname': 'patch_error_test',
            'password': 'test',
        }
        self._patch()

        self._assert_failure(400, 'It contains requests for fields that do not exist or cannot be modified.')

    @freeze_time(FREEZE_TIME)
    def test_delete(self):
        self._delete()
        self._user = Shopper.objects.get(id=self._user.id)

        self._assert_success_with_id_response()
        self.assertEqual(self._response_data['id'], self._user.id)
        self.assertTrue(not self._user.is_active)
        self.assertEqual(datetime_to_iso(self._user.deleted_at), FREEZE_TIME)


class WholesalerViewTestCase(ViewTestCase):
    pass


class ChangePasswordTestCase(ViewTestCase):
    pass


class IsUniqueTestCase(ViewTestCase):
    pass