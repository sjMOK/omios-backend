from .test_cases import ModelTestCase
from ..models import TemporaryImage
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
