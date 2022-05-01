import json
from unittest.mock import patch
from PIL import Image
from tempfile import NamedTemporaryFile

from django.utils.module_loading import import_string

from rest_framework.test import APISimpleTestCase, APITestCase
from rest_framework.exceptions import APIException, ValidationError

from common.utils import BASE_IMAGE_URL
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

    @classmethod
    def _get_default_model_after_creation(cls, data=None):
        if data is None:
            data = cls._test_data

        return cls._model_class.objects.create(**data)

    def _get_model(self):
        return self._model_class(**self._test_data)

    def _get_model_after_creation(self):
        return self._get_default_model_after_creation(self._test_data)


class SerializerTestCase(APITestCase):
    _serializer_class = None

    def __init__(self, *args, **kwargs):
        if self._serializer_class is None:
            raise APIException('_serializer_class variable must be written.')

        super().__init__(*args, **kwargs)

    def _get_serializer(self, *args, **kwargs):
        return self._serializer_class(*args, **kwargs)

    def _get_serializer_after_validation(self, *args, **kwargs):
        serializer = self._get_serializer(*args, **kwargs)
        serializer.is_valid()

        return serializer

    def _test_model_instance_serialization(self, instance, expected_data, context={}):
        self.assertDictEqual(self._get_serializer(instance, context=context).data, expected_data)

    def _test_serializer_raise_validation_error(self, expected_message, *args, **kwargs):
        self.assertRaisesMessage(
            ValidationError,
            expected_message,
            self._get_serializer(*args, **kwargs).is_valid,
            raise_exception=True
        )

    def _test_validated_data(self, data, expected_validated_data):
        serializer = self._get_serializer_after_validation(data=data)

        self.assertDictEqual(serializer.validated_data, expected_validated_data)


class ListSerializerTestCase(SerializerTestCase):
    _child_serializer_class = None

    def __init__(self, *args, **kwargs):
        if self._child_serializer_class is None:
            raise APIException('_child_serializer_class variable must be written.')

        self._serializer_class = self._child_serializer_class
        self._list_serializer_class = self._child_serializer_class.Meta.list_serializer_class

        super().__init__(*args, **kwargs)

    def _get_serializer(self, *args, **kwargs):
        return self._serializer_class(many=True, *args, **kwargs)


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

    def __create_images(self, size):
        self.__images = []
        for i in range(size):
            image = Image.new('RGB', (100,100))
            file = NamedTemporaryFile(suffix='.jpg' if i % 2 else '.png')
            image.save(file)
            self.__images.append(open(file.name, 'rb'))

        return self.__images

    def __delete_images(self):
        for i in range(len(self.__images)):
            self.__images[i].close()

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

    @patch('common.storage.MediaStorage.save')
    def _test_image_upload(self, mock, size=1, middle_path=''):
        self.__create_images(size)
        self._post({'image': self.__images})
        self.__delete_images()

        self._assert_success()
        self.assertEqual(mock.call_count, size)
        self.assertEqual(len(self._response_data['image']), size)
        self.assertTrue(self._response_data['image'][0].startswith(BASE_IMAGE_URL))
        self.assertIn(middle_path, self._response_data['image'][0])

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
