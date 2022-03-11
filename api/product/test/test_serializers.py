from rest_framework.serializers import Serializer, CharField, IntegerField
from rest_framework.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase

import random

from common.utils import BASE_IMAGE_URL
from common.test.test_cases import SerializerTestCase, FunctionTestCase
from ..serializers import (
    ProductWriteSerializer, validate_require_data_in_partial_update, has_duplicate_element, is_delete_data, is_update_data, 
    is_create_data, SubCategorySerializer, MainCategorySerializer, ColorSerializer, SizeSerializer,
    LaundryInformationSerializer, ThicknessSerializer, SeeThroughSerializer, FlexibilitySerializer,
    AgeSerializer, StyleSerializer, MaterialSerializer, ProductImagesSerializer, get_list_of_single_item, get_create_or_update_attrs,
    get_update_or_delete_attrs, ProductImagesListSerializer
)
from .factory import (
    ProductFactory, SubCategoryFactory, MainCategoryFactory, ColorFactory, SizeFactory, LaundryInformationFactory,
    ThicknessFactory, SeeThroughFactory, FlexibilityFactory, AgeFactory, StyleFactory, MaterialFactory,
    ProductImagesFactory
)
from ..validators import validate_url


class ValidateRequireDataInPartialUpdateTestCase(FunctionTestCase):
    _function = validate_require_data_in_partial_update

    class DummySerializer(Serializer):
        age_not_required = IntegerField(required=False)
        name_required = CharField()

    def test(self):
        data = {}
        serializer = self.DummySerializer(data=data, partial=True)

        self.assertRaisesRegex(
            ValidationError,
            r'name_required field is required.',
            self._call_function,
            data=data, fields=serializer.fields
        )


class HasDuplicateElementTestCase(FunctionTestCase):
    _function = has_duplicate_element

    def test_duplicated_array(self):
        array = [1, 2, 2, 3]

        self.assertTrue(self._call_function(array))

    def test_not_duplicated_array(self):
        array = [1, 2, 3]

        self.assertTrue(not self._call_function(array))


class IsCreateDeleteUpdateDataTestCases(APISimpleTestCase):
    def setUp(self):
        self.create_data = {
            'name': 'omios',
            'age': 1,
        }
        self.update_data = {
            'id': 100,
            'name': 'omios',
            'age': 1,
        }
        self.delete_data = {
            'id': 100,
        }
    
    def test_is_create_data(self):
        self.assertTrue(is_create_data(self.create_data))
        self.assertTrue(not is_create_data(self.update_data))
        self.assertTrue(not is_create_data(self.delete_data))

    def test_is_update_data(self):
        self.assertTrue(not is_update_data(self.create_data))
        self.assertTrue(is_update_data(self.update_data))
        self.assertTrue(not is_update_data(self.delete_data))

    def test_is_delete_data(self):
        self.assertTrue(not is_delete_data(self.create_data))
        self.assertTrue(not is_delete_data(self.update_data))
        self.assertTrue(is_delete_data(self.delete_data))


class GetAttrsTestCase(APISimpleTestCase):
    def setUp(self):
        self.create_attrs = [
            {'name': 'name1', 'age': 1},
            {'name': 'name2', 'age': 2},
        ]
        self.update_attrs = [
            {'id': 100, 'name': 'name100', 'age': 100},
            {'id': 101, 'name': 'name101', 'age': 101},
        ]
        self.delete_attrs = [
            {'id': 200},
            {'id': 201},
        ]
        self.attrs = self.create_attrs + self.update_attrs + self.delete_attrs
    
    def test_get_create_or_update_attrs(self):
        create_or_update_attrs = self.create_attrs + self.update_attrs

        self.assertListEqual(get_create_or_update_attrs(self.attrs), create_or_update_attrs)

    def test_get_update_or_delete_attrs(self):
        update_or_delete_attrs = self.update_attrs + self.delete_attrs

        self.assertListEqual(get_update_or_delete_attrs(self.attrs), update_or_delete_attrs)


class GetListOfSingleItem(FunctionTestCase):
    _function = get_list_of_single_item

    def test(self):
        attrs = [
            {'id': 1, 'name': 'name1'},
            {'id': 2, 'name': 'name2'},
            {'id': 3, 'name': 'name3'},
            {'id': 4, 'name': 'name4'},
        ]

        self.assertEqual(self._call_function('id', attrs), [1, 2, 3, 4])


class SubCategorySerializerTestCase(SerializerTestCase):
    _serializer_class = SubCategorySerializer

    def test_model_instance_serialization(self):
        sub_category = SubCategoryFactory()
        expected_data = {
            'id': sub_category.id,
            'name': sub_category.name,
        }

        self._test_model_instance_serialization(sub_category, expected_data)


class MainCategorySerializerTestCase(SerializerTestCase):
    _serializer_class = MainCategorySerializer

    def test_model_instance_serialization(self):
        main_category = MainCategoryFactory()
        SubCategoryFactory.create_batch(3, main_category=main_category)
        expected_data = {
            'id': main_category.id,
            'name': main_category.name,
            'image_url': main_category.image_url.url,
            'sub_category': [
                {'id': sub_category.id, 'name': sub_category.name} 
                for sub_category in main_category.sub_categories.all()
            ],
        }

        self._test_model_instance_serialization(main_category, expected_data)


class ColorSerializerTestCase(SerializerTestCase):
    _serializer_class = ColorSerializer

    def test_model_instance_serialization(self):
        color = ColorFactory()
        expected_data = {
            'id': color.id,
            'name': color.name,
            'image_url': color.image_url.url,
        }

        self._test_model_instance_serialization(color, expected_data)


class SizeSerializerTestCase(SerializerTestCase):
    _serializer_class = SizeSerializer

    def test_model_instance_serialization(self):
        size = SizeFactory()
        expected_data = {
            'id': size.id,
            'name': size.name,
        }

        self._test_model_instance_serialization(size, expected_data)


class LaundryInformationSerializerTestCase(SerializerTestCase):
    _serializer_class = LaundryInformationSerializer

    def test_model_instance_serialization(self):
        laundry_information = LaundryInformationFactory()
        expected_data = {
            'id': laundry_information.id,
            'name': laundry_information.name,
        }

        self._test_model_instance_serialization(laundry_information, expected_data)


class ThicknessSerializerTestCase(SerializerTestCase):
    _serializer_class = ThicknessSerializer

    def test_model_instance_serialization(self):
        thickness = ThicknessFactory()
        expected_data = {
            'id': thickness.id,
            'name': thickness.name,
        }

        self._test_model_instance_serialization(thickness, expected_data)


class SeeThroughSerializerTestCase(SerializerTestCase):
    _serializer_class = SeeThroughSerializer

    def test_model_instance_serialization(self):
        see_through = SeeThroughFactory()
        expected_data = {
            'id': see_through.id,
            'name': see_through.name,
        }

        self._test_model_instance_serialization(see_through, expected_data)


class FlexibilitySerializerTestCase(SerializerTestCase):
    _serializer_class = FlexibilitySerializer

    def test_model_instance_serialization(self):
        flexibility = FlexibilityFactory()
        expected_data = {
            'id': flexibility.id,
            'name': flexibility.name,
        }

        self._test_model_instance_serialization(flexibility, expected_data)


class AgeSerializerTestCase(SerializerTestCase):
    _serializer_class = AgeSerializer

    def test_model_instance_serialization(self):
        age = AgeFactory()
        expected_data = {
            'id': age.id,
            'name': age.name,
        }

        self._test_model_instance_serialization(age, expected_data)


class StyleSerializerTestCase(SerializerTestCase):
    _serializer_class = StyleSerializer

    def test_model_instance_serialization(self):
        style = StyleFactory()
        expected_data = {
            'id': style.id,
            'name': style.name,
        }

        self._test_model_instance_serialization(style, expected_data)


class MaterialSerializerTestCase(SerializerTestCase):
    _serializer_class = MaterialSerializer

    def test_model_instance_serialization(self):
        material = MaterialFactory()
        expected_data = {
            'id': material.id,
            'name': material.name,
        }

        self._test_model_instance_serialization(material, expected_data)


class ProductImagesSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductImagesSerializer

    @classmethod
    def setUpTestData(cls):
        cls.product_images = ProductImagesFactory()

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product_images.id,
            'image_url': BASE_IMAGE_URL + self.product_images.image_url,
            'sequence': self.product_images.sequence,
        }

        self._test_model_instance_serialization(self.product_images, expected_data)

    def test_desrialization(self):
        data = {
            'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_1.jpg',
            'sequence': 1
        }
        expected_validated_data = {
            'image_url': validate_url(data['image_url']),
            'sequence': 1
        }
        serializer = self._get_serializer_after_validation(data=data)

        self.assertDictEqual(serializer.validated_data, expected_validated_data)

    def __test_validate_image_url(self, image_url, expected_message):
        data = {
            'image_url': image_url,
            'sequence': 1,
        }
        serializer = self._get_serializer(data=data)

        self.assertRaisesMessage(
            ValidationError,
            expected_message,
            serializer.is_valid,
            raise_exception=True
        )

    def test_validate_image_url_not_starts_with_BASE_IMAGE_URL_failure(self):
        image_url = 'https://omios.com/product/sample/product_1.jpg'

        self.__test_validate_image_url(
            image_url, expected_message='Enter a valid BASE_IMAGE_URL.'
        )

    def test_validate_image_url_object_not_found(self):
        image_url = BASE_IMAGE_URL + 'product/sample/product_-999.jpg'

        self.__test_validate_image_url(
            image_url, expected_message='object not found.'
        )

    def __test_validate_partial_update_does_not_include_all_data(self, data, expected_message):
        serializer = self._get_serializer(self.product_images, data=data, partial=True)

        self.assertRaisesMessage(
            ValidationError,
            expected_message,
            serializer.is_valid,
            raise_exception=True
        )

    def test_validate_partial_update_does_not_include_all_data_with_create_data(self):
        data = {'image_url': BASE_IMAGE_URL + 'product/sample/product_1.jpg'}

        self.__test_validate_partial_update_does_not_include_all_data(
            data, 'sequence field is required.'
        )

    def test_validate_partial_update_does_not_include_all_data_with_update_data(self):
        data = {
            'id': 1,
            'sequence': 1,
        }

        self.__test_validate_partial_update_does_not_include_all_data(
            data, 'image_url field is required.'
        )


class ProductImagesListSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductImagesSerializer
    list_serializer_class = ProductImagesListSerializer

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.product_images = [
            ProductImagesFactory(product=cls.product, sequence=i)
            for i in range(1, 6)
        ]
        cls.length_upper_limit = cls.list_serializer_class.length_upper_limit

    def _get_serializer(self, *args, **kwargs):
        return super()._get_serializer(many=True, *args, **kwargs)

    def __get_update_data(self, data):
        data = {
            'images': data
        }

        return data

    def __test_validate_raise_validation_error(self, serializer, expected_message):
        self.assertRaisesMessage(
            ValidationError,
            expected_message,
            serializer.is_valid,
            raise_exception=True
        )

    def __test_validate_create_raise_validation_error(self, data, expected_message):
        serializer = self._get_serializer(data=data)
        self.__test_validate_raise_validation_error(serializer, expected_message)

    def __test_validate_update_raise_validation_error(self, data, expected_message):
        data = self.__get_update_data(data)
        serializer = ProductWriteSerializer(
            self.product, data, partial=True
        )

        self.__test_validate_raise_validation_error(serializer, expected_message)

    def __test_validate_create_wrong_sequence_ascending_order(self, sequences):
        data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(index+1),
                'sequence': sequence,
            }for index, sequence in enumerate(sequences)
        ]
        expected_message = 'The sequence of the images must be ascending from 1 to n.'

        self.__test_validate_create_raise_validation_error(data, expected_message)
    
    def test_serialization(self):
        expected_data = [
            {
                'id': product_image.id,
                'image_url': BASE_IMAGE_URL + product_image.image_url,
                'sequence': product_image.sequence,
            }
            for product_image in self.product_images
        ]
        serializer = self._get_serializer(self.product_images)

        self.assertListEqual(expected_data, serializer.data)

    def test_desrialization(self):
        data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(i),
                'sequence': i,
            }for i in range(1, 11)
        ]
        expected_validated_data = [
            {
                'image_url': validate_url(d['image_url']),
                'sequence': d['sequence'],
            }for d in data
        ]
        serializer = self._get_serializer_after_validation(data=data)

        self.assertListEqual(expected_validated_data, serializer.validated_data)

    def test_validate_create_input_data_length_must_more_than_upper_limit(self):
        data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(i+1),
                'sequence': i,
            } for i in range(self.length_upper_limit + 1)
        ]
        expected_message = 'The product cannot have more than ten images.'

        self.__test_validate_create_raise_validation_error(data, expected_message)

    def test_validate_create_sequences_not_startswith_one(self):
        sequences = range(5)
        self.__test_validate_create_wrong_sequence_ascending_order(sequences)

    def test_validate_create_omitted_sequences(self):
        sequences = list(range(1, 6))
        sequences.pop(3)
        self.__test_validate_create_wrong_sequence_ascending_order(sequences)

    def test_validate_update_does_not_pass_all_image_data(self):
        data = [
            {
                'id': product_image.id,
                'image_url': BASE_IMAGE_URL + product_image.image_url, 
                'sequence': product_image.sequence,
            }
            for product_image in self.product_images
        ]
        data.pop(random.randint(0, len(data)-1))
        expected_message = 'You must contain all image data that the product has.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_does_not_pass_exact_image_data(self):
        data = [
            {
                'id': random.randint(1, 10000),
                'image_url': BASE_IMAGE_URL + product_image.image_url, 
                'sequence': product_image.sequence,
            }
            for product_image in self.product_images
        ]
        expected_message = 'You must contain all image data that the product has.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_input_data_length_must_more_than_upper_limit(self):
        update_data = [
            {
                'id': product_image.id,
                'image_url': BASE_IMAGE_URL + product_image.image_url,
                'sequence': product_image.sequence,
            }
            for product_image in self.product_images
        ]
        create_data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(i),
                'sequence': i,
            } for i in range(len(self.product_images)+1, self.length_upper_limit+2)
        ]
        data = update_data + create_data
        expected_message = 'The product cannot have more than ten images.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_input_data_length_less_than_zero(self):
        data = [
            {'id': product_image.id} 
            for product_image in self.product_images
        ]
        expected_message = 'The product must have at least one image.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_sequences_not_startswith_one(self):
        update_data = [
            {
                'id': product_image.id,
                'image_url': BASE_IMAGE_URL + product_image.image_url,
                'sequence': product_image.sequence - 1,
            }
            for product_image in self.product_images
        ]
        create_data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(i),
                'sequence': i,
            } for i in range(len(self.product_images)+1, self.length_upper_limit)
        ]
        data = update_data + create_data
        expected_message = 'The sequence of the images must be ascending from 1 to n.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_omitted_sequences(self):
        update_data = [
            {
                'id': product_image.id,
                'image_url': BASE_IMAGE_URL + product_image.image_url,
                'sequence': product_image.sequence,
            }
            for product_image in self.product_images
        ]
        create_data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(i),
                'sequence': i,
            } for i in range(len(self.product_images)+2, self.length_upper_limit)
        ]

        data = update_data + create_data
        expected_message = 'The sequence of the images must be ascending from 1 to n.'

        self.__test_validate_update_raise_validation_error(data, expected_message)
