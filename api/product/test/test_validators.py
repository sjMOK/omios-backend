from rest_framework.exceptions import ValidationError

from common.test.test_cases import FunctionTestCase
from common.utils import BASE_IMAGE_URL
from ..validators import validate_url, validate_sequence_ascending_order


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
            image_url, 'object not found.'
        )

    def test_return_value(self):
        image_url_suffix = 'product/sample/product_1.jpg'
        image_url = BASE_IMAGE_URL + image_url_suffix

        self.assertEqual(self._call_function(image_url), image_url_suffix)


class ValidateSequenceAscendingOrderTestCase(FunctionTestCase):
    _function = validate_sequence_ascending_order

    def __test_validate_sequence(self, sequences):
        self.assertRaisesRegex(
            ValidationError,
            r'The sequence of the images must be ascending from 1 to n.',
            validate_sequence_ascending_order,
            sequences
        )

    def test_sequences_startswith_zero(self):
        sequences = list(range(5))

        self.__test_validate_sequence(sequences)

    def test_omitted_sequences(self):
        sequences = list(range(1, 6))
        sequences.pop(3)

        self.__test_validate_sequence(sequences)
