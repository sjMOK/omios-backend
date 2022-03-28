from rest_framework.exceptions import ValidationError

from common.test.test_cases import FunctionTestCase
from common.utils import BASE_IMAGE_URL
from ..validators import validate_url


class ValidateURLTestCase(FunctionTestCase):
    _function = validate_url

    def __test_validate(self, image_url, expected_message):
        self.assertRaisesMessage(
            ValidationError,
            expected_message,
            self._call_function,
            image_url
        )

    def test_validate_image_url_not_starts_with_BASE_IMAGE_URL_failure(self):
        image_url = 'https://omios.com/product/sample/product_1.jpg'

        self.__test_validate(
            image_url, 'Enter a valid BASE_IMAGE_URL.'
        )

    def test_validate_image_url_object_not_found(self):
        image_url = BASE_IMAGE_URL + 'product/sample/product_-999.jpg'

        self.__test_validate(
            image_url, 'Not found.'
        )

    def test_return_value(self):
        image_url_suffix = 'product/sample/product_1.jpg'
        image_url = BASE_IMAGE_URL + image_url_suffix

        self.assertEqual(self._call_function(image_url), image_url_suffix)
