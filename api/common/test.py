from rest_framework.test import APITestCase
from rest_framework.exceptions import APIException


class ModelTestCase(APITestCase):
    _model_class = None

    def __init__(self, *args, **kwargs):
        if self._model_class is None:
            raise APIException('_model_class must be written.')

        super().__init__(*args, **kwargs)

    def _get_model(self):
        return self._model_class(**self.test_data)

    def _get_model_after_creation(self):
        return self._model_class.objects.create(**self.test_data)


class SerializerTestCase(APITestCase):
    _serializer_class = None

    def __init__(self, *args, **kwargs):
        if self._serializer_class is None:
            raise APIException('_serializer_class must be written')

        super().__init__(*args, **kwargs)

    def _get_serializer(self, **kwargs):
        return self._serializer_class(**kwargs)


class ViewTestCase(APITestCase):
    pass
