from django.forms import model_to_dict

from .test_cases import ModelTestCase
from .factories import SettingGroupFactory
from ..models import TemporaryImage, SettingGroup, SettingItem
from ..utils import DEFAULT_IMAGE_URL


class TemporaryImageTestCase(ModelTestCase):
    _model_class = TemporaryImage

    def setUp(self):
        self._test_data = {
            'image_url': DEFAULT_IMAGE_URL,
        }
    
    def test_create(self):
        temporary_image = self._get_model_after_creation()

        self.assertEqual(temporary_image.image_url, self._test_data['image_url'])


class SettingGroupTestCase(ModelTestCase):
    _model_class = SettingGroup

    def setUp(self):
        self._test_data = {
            'app': 'test_app',
            'name': 'test_name',
            'main_key': 'test_main_key',
            'sub_key': 'test_sub_key',
        }

    def test_create(self):
        setting_group = self._get_model_after_creation()

        self.assertDictEqual(model_to_dict(setting_group, exclude=['id']), self._test_data)


class SettingItemTestCase(ModelTestCase):
    _model_class = SettingItem

    def setUp(self):
        self._test_data = {
            'group': SettingGroupFactory(),
            'name': 'test_name',
        }

    def test_create(self):
        setting_item = self._get_model_after_creation()

        self.assertDictEqual(model_to_dict(setting_item, exclude=['id']), {
            **self._test_data,
            'group': self._test_data['group'].id,
        })