import json

from django.utils.module_loading import import_string

from rest_framework.serializers import ModelSerializer
from rest_framework.test import APISimpleTestCase, APITestCase
from rest_framework.exceptions import APIException

from user.test.factory import UserFactory, ShopperFactory, WholesalerFactory


FREEZE_TIME = '2021-11-20T01:02:03.456789'
FREEZE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
FREEZE_TIME_AUTO_TICK_SECONDS = 10


class FunctionTestCase(APISimpleTestCase):
    _function = None

    def __init__(self, *args, **kwargs):
        if self._function is None:
            raise APIException('_function variable must be written.')

        self._function = import_string('%s.%s' % (self._function.__module__, self._function.__name__))
        
        super().__init__(*args, **kwargs)

    def _call_function(self, *args, **kwargs):
        return self._function(*args, **kwargs)


class ModelTestCase(APITestCase):
    _model_class = None
    test_create = None

    def __init__(self, *args, **kwargs):
        if self._model_class is None:
            raise APIException('_model_class variable must be written.')

        if self.test_create is None:
            raise APIException('test_create method must be written.')

        super().__init__(*args, **kwargs)

    def _get_model(self):
        return self._model_class(**self._test_data)

    def _get_model_after_creation(self):
        return self._model_class.objects.create(**self._test_data)


class SerializerTestCase(APITestCase):
    _serializer_class = None

    def __init__(self, *args, **kwargs):
        if self._serializer_class is None:
            raise APIException('_serializer_class variable must be written.')

        if issubclass(self._serializer_class, ModelSerializer) and not isinstance(self, ModelSerializerTestCase):
            raise APIException('Instead of this class, ModelSerializerTestCase must be inherited.')

        super().__init__(*args, **kwargs)

    def _get_serializer(self, **kwargs):
        return self._serializer_class(**kwargs)


class ModelSerializerTestCase(SerializerTestCase):
    test_model_instance_serialization = None

    def __init__(self, *args, **kwargs):
        if self.test_model_instance_serialization is None:
            raise APIException('test_model_instance_serialization method must be written.')

        super().__init__(*args, **kwargs)

    def _test_model_instance_serialization(self, instance, expected_data):  
        self.assertDictEqual(super()._get_serializer(instance=instance).data, expected_data)


class ViewTestCase(APITestCase):
    _url = None
    _test_data = {}

    def __init__(self, *args, **kwargs):
        if self._url is None:
            raise APIException('_url must be written.')

        super().__init__(*args, **kwargs)

    @classmethod
    def _create_shopper(cls, size=1):
        return ShopperFactory.create_batch(size)

    @classmethod
    def _create_wholesaler(cls, size=1):
        return WholesalerFactory.create_batch(size)

    @classmethod
    def _set_user(cls):
        cls._user = UserFactory()

    @classmethod
    def _set_shopper(cls, user=None):
        if user is None:
            user = cls._create_shopper()[0]
        cls._user = user

    @classmethod
    def _set_wholesaler(cls, user=None):
        if user is None:
            user = cls._create_wholesaler()[0]
        cls._user = user

    def _set_authentication(self):
        self.client.force_authenticate(user=self._user)

    def _unset_authentication(self):
        self.client.force_authenticate(user=None)

    def __set_response(self, response, expected_success_status_code):
        self._response = response
        self._response_body = json.loads(response.content)
        self._response_data = self._response_body['data'] if 'data' in self._response_body else None
        self.__expected_success_status_code = expected_success_status_code

    def _get(self, data={}, *args, **kwargs):
        self.__set_response(self.client.get(self._url, dict(self._test_data, **data), *args, **kwargs), 200)

    def _post(self, data={}, *args, **kwargs):
        self.__set_response(self.client.post(self._url, dict(self._test_data, **data), *args, **kwargs), 201)

    def _patch(self, data={}, *args, **kwargs):
        self.__set_response(self.client.patch(self._url, dict(self._test_data, **data), *args, **kwargs), 200)
    
    def _delete(self, data={}, *args, **kwargs):
        self.__set_response(self.client.delete(self._url, dict(self._test_data, **data), *args, **kwargs), 200)

    def __assert_default_response(self, expected_status_code, expected_message):
        self.assertEqual(self._response.status_code, expected_status_code)
        self.assertEqual(self._response_body['code'], expected_status_code)
        self.assertEqual(self._response_body['message'], expected_message)

    def _assert_success(self):
        self.__assert_default_response(self.__expected_success_status_code, 'success')
        self.assertTrue('data' in self._response_body)

    def _assert_success_with_id_response(self):
        self._assert_success()
        self.assertTrue(not set(self._response_data).difference(set(['id'])))
        self.assertIsInstance(self._response_data['id'], int)

    def _assert_success_with_is_unique_response(self, is_unique):
        self._assert_success()
        self.assertTrue(not set(self._response_data).difference(set(['is_unique'])))
        self.assertIsInstance(self._response_data['is_unique'], bool)
        self.assertEqual(self._response_data['is_unique'], is_unique)

    def _assert_failure(self, expected_failure_status_code, expected_message):
        self.__assert_default_response(expected_failure_status_code, expected_message)
        self.assertTrue('data' not in self._response_body)
