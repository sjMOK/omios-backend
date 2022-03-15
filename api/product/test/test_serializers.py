import random, copy

from rest_framework.serializers import Serializer, CharField, IntegerField
from rest_framework.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase

from common.utils import BASE_IMAGE_URL
from common.test.test_cases import FunctionTestCase, SerializerTestCase, ListSerializerTestCase
from ..validators import validate_url
from ..serializers import (
    validate_require_data_in_partial_update, has_duplicate_element, is_create_data, is_update_data, is_delete_data, get_list_of_single_item,
    get_create_or_update_attrs, get_update_or_delete_attrs, ProductMaterialSerializer, ProductWriteSerializer, SubCategorySerializer,
    MainCategorySerializer, ColorSerializer, SizeSerializer, LaundryInformationSerializer, ThicknessSerializer, SeeThroughSerializer,
    FlexibilitySerializer, AgeSerializer, StyleSerializer, MaterialSerializer, ProductImagesSerializer, ProductColorSerializer, 
    OptionSerializer,
)
from .factory import (
    ProductColorFactory, ProductFactory, SubCategoryFactory, MainCategoryFactory, ColorFactory, SizeFactory, LaundryInformationFactory,
    ThicknessFactory, SeeThroughFactory, FlexibilityFactory, AgeFactory, StyleFactory, MaterialFactory, ProductImagesFactory,
    ProductMaterialFactory, OptionFactory,
)

SAMPLE_PRODUCT_IMAGE_URL = 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_1.jpg'


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
        cls.data = {
            'image_url': SAMPLE_PRODUCT_IMAGE_URL,
            'sequence': 1
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product_images.id,
            'image_url': BASE_IMAGE_URL + self.product_images.image_url,
            'sequence': self.product_images.sequence,
        }

        self._test_model_instance_serialization(self.product_images, expected_data)

    def test_deserialization(self):
        expected_validated_data = {
            'image_url': validate_url(self.data['image_url']),
            'sequence': self.data['sequence']
        }

        self._test_deserialzation(self.data, expected_validated_data)

    def test_validate_image_url_value(self):
        serializer = self._get_serializer_after_validation(data=self.data)
        
        self.assertEqual(
            serializer.validated_data['image_url'],
            validate_url(self.data['image_url'])
        )

    def __test_validate_image_url(self, image_url, expected_message):
        self.data['image_url'] = image_url
        serializer = self._get_serializer(data=self.data)

        self._test_serializer_raise_validation_error(serializer, expected_message)

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

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_validate_partial_update_does_not_include_all_data_with_create_data(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)

        self.__test_validate_partial_update_does_not_include_all_data(
            self.data, '{0} field is required.'.format(key)
        )

    def test_validate_partial_update_does_not_include_all_data_with_update_data(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        self.data['id'] = 100

        self.__test_validate_partial_update_does_not_include_all_data(
            self.data, '{0} field is required.'.format(key)
        )


class ProductImagesListSerializerTestCase(ListSerializerTestCase):
    _serializer_class = ProductImagesSerializer

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.product_images = [
            ProductImagesFactory(product=cls.product, sequence=i)
            for i in range(1, 6)
        ]
        cls.length_upper_limit = cls.get_list_serializer_class().length_upper_limit

    def __get_update_data(self, data):
        data = {
            'images': data
        }

        return data

    def __test_validate_raise_validation_error(self, serializer, expected_message):
        self._test_serializer_raise_validation_error(serializer, expected_message)

    def __test_validate_create_raise_validation_error(self, data, expected_message):
        serializer = self._get_serializer(data=data)
        self.__test_validate_raise_validation_error(serializer, expected_message)

    def __test_validate_update_raise_validation_error(self, data, expected_message):
        data = self.__get_update_data(data)
        serializer = ProductWriteSerializer(
            self.product, data=data, partial=True
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

    def test_raise_valid_error_data_length_more_than_upper_limit_in_create(self):
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


class ProductMaterialSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductMaterialSerializer

    @classmethod
    def setUpTestData(cls):
        cls.product_material = ProductMaterialFactory()
        cls.data = {
            'material': '가죽',
            'mixing_rate': 100
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product_material.id,
            'material': self.product_material.material,
            'mixing_rate': self.product_material.mixing_rate,
        }

        self._test_model_instance_serialization(self.product_material, expected_data)

    def test_deserialization(self):
        expected_validated_data = {
            'material': self.data['material'],
            'mixing_rate': self.data['mixing_rate'],
        }

        self._test_deserialzation(self.data, expected_validated_data)

    def __test_validate_partial_update_does_not_include_all_data(self, data, expected_message):
        serializer = self._get_serializer(self.product_material, data=data, partial=True)

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_validate_partial_update_does_not_include_all_data_with_create_data(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)

        self.__test_validate_partial_update_does_not_include_all_data(
            self.data, '{0} field is required.'.format(key)
        )

    def test_validate_partial_update_does_not_include_all_data_with_update_data(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        self.data['id'] = 100

        self.__test_validate_partial_update_does_not_include_all_data(
            self.data, '{0} field is required.'.format(key)
        )


class ProductMaterialListSerializerTestCase(ListSerializerTestCase):
    _serializer_class = ProductMaterialSerializer
    materials_num = 5

    @classmethod
    def setUpTestData(cls):
        total_mixing_rate_value = cls.get_list_serializer_class().sum_of_mixing_rates
        mixing_rate = total_mixing_rate_value / cls.materials_num

        cls.product = ProductFactory()
        cls.product_materials = ProductMaterialFactory.create_batch(
            cls.materials_num, product=cls.product, mixing_rate=mixing_rate
        )

        cls.create_data = [
            {
                'material': 'material_{0}'.format(i),
                'mixing_rate': mixing_rate
            }for i in range(cls.materials_num)
        ]

        cls.update_data = [
            {
                'id': product_material.id,
                'material': product_material.material,
                'mixing_rate': product_material.mixing_rate
            }for product_material in cls.product_materials
        ]

    def __get_update_data(self, data):
        data = {
            'materials': data
        }

        return data

    def __test_validate_create_raise_validation_error(self, data, expected_message):
        serializer = self._get_serializer(data=data)

        self._test_serializer_raise_validation_error(serializer, expected_message)
        
    def __test_validate_update_raise_validation_error(self, data, expected_message):
        data = self.__get_update_data(data)
        serializer = ProductWriteSerializer(
            self.product, data=data, partial=True
        )

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_validate_create_total_mixing_rates_does_not_match_criteria(self):
        data = self.create_data
        data[0]['mixing_rate'] += 10

        expected_message = 'The total of material mixing rates must be 100.'

        self.__test_validate_create_raise_validation_error(data, expected_message)

    def test_validate_create_duplicated_material_name(self):
        data = self.create_data
        index = random.choice(range(1, len(data)))
        data[index]['material'] = data[0]['material']

        expected_message = 'Material is duplicated.'

        self.__test_validate_create_raise_validation_error(data, expected_message)

    def test_validate_update_does_not_pass_all_material_data(self):
        data = self.update_data
        data.pop(random.randint(0, len(data)-1))

        expected_message = 'You must contain all material data that the product has.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_does_not_pass_exact_image_data(self):
        data = self.update_data
        id_min_value = min([d['id'] for d in data])
        data[0]['id'] = id_min_value - 1

        expected_message = 'You must contain all material data that the product has.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_validate_update_total_mixing_rates_exceed_criteria(self):
        data = self.create_data + self.update_data

        for d in data:
            d['mixing_rate'] = self.list_serializer_class.sum_of_mixing_rates / len(data)

        index = random.choice(range(len(data)))
        data[index]['mixing_rate'] += 10

        expected_message = 'The total of material mixing rates must be 100.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_raise_validation_error_total_mixing_rates_less_than_criteria_in_update(self):
        self.update_data[-1] = {'id': self.update_data[-1]['id']}
        data = self.create_data + self.update_data

        for d in data:
            if not is_delete_data(d):
                d['mixing_rate'] = self.list_serializer_class.sum_of_mixing_rates / len(data)

        expected_message = 'The total of material mixing rates must be 100.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_raise_validation_error_duplicated_material_name_in_update(self):
        data = self.create_data + self.update_data

        for d in data:
            d['mixing_rate'] = self.list_serializer_class.sum_of_mixing_rates / len(data)

        index = random.choice(range(1, len(data)))
        data[index]['material'] = data[0]['material']

        expected_message = 'Material is duplicated.'

        self.__test_validate_update_raise_validation_error(data, expected_message)


class OptionSerializerTestCase(SerializerTestCase):
    _serializer_class = OptionSerializer

    @classmethod
    def setUpTestData(cls):
        size = SizeFactory()
        cls.option = OptionFactory(size = size.name)
        cls.data = {
            'size': 'Free',
            'price_difference': 0
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.option.id, 
            'size': self.option.size,
            'price_difference': self.option.price_difference,
        }

        self._test_model_instance_serialization(self.option, expected_data)

    def test_deserialization(self):
        expected_validated_data = {
            'size': self.data['size'],
            'price_difference': self.data['price_difference']
        }

        self._test_deserialzation(self.data, expected_validated_data)

    def test_raise_validation_error_create_data_does_not_include_all_data_in_partial(self):
        self.data.pop('size')
        serializer = self._get_serializer(data=self.data, partial=True)
        expected_message = '{0} field is required.'.format('size')

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_validation_error_update_size_data(self):
        data = {
            'id': self.option.id,
            'size': self.option.size + '_update',
            'price_difference': self.option.price_difference
        }
        serializer = self._get_serializer(data=data, partial=True)
        expected_message = 'Size data cannot be updated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)


class OptionListSerializerTestCase(ListSerializerTestCase):
    _serializer_class = OptionSerializer
    options_num = 3

    @classmethod
    def setUpTestData(cls):
        cls.product_color = ProductColorFactory()
        cls.options = OptionFactory.create_batch(size=cls.options_num, product_color=cls.product_color)
        cls.create_data = [
            {
                'size': 'size_{0}'.format(i),
                'price_difference': random.randint(0, cls.product_color.product.price * 0.2)
            }
            for i in range(cls.options_num)
        ]
        cls.update_data = [
            {
                'id': option.id,
                'size': option.size,
                'price_difference': option.price_difference
            }for option in cls.options
        ]

    def __test_duplicated_size_data(self, data):
        index = random.choice(range(1, len(data)))
        data[index]['size'] = data[0]['size']

        serializer = self._get_serializer(data=data)
        expected_message = 'size is duplicated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_validation_error_duplicated_size_data_in_create(self):
        data = self.create_data

        self.__test_duplicated_size_data(data)

    def test_raise_validation_error_duplicated_size_data_in_update(self):
        data = self.update_data + self.create_data
        
        self.__test_duplicated_size_data(data)
    

class ProductColorSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductColorSerializer
    options_num = 4

    @classmethod
    def setUpTestData(cls):
        cls.product_color = ProductColorFactory()
        cls.options = OptionFactory.create_batch(
            size=cls.options_num, product_color=cls.product_color
        )
        cls.data = {
            'display_color_name': 'deepblue',
            'color': cls.product_color.color.id,
            'options': [
                {
                    'size': option.size,
                    'price_difference': option.price_difference
                }for option in cls.options
            ],
            'image_url': SAMPLE_PRODUCT_IMAGE_URL,
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product_color.id,
            'display_color_name': self.product_color.display_color_name,
            'color': self.product_color.color.id,
            'options': OptionSerializer(self.options, many=True).data,
            'image_url': BASE_IMAGE_URL + self.product_color.image_url,
        }
        self._test_model_instance_serialization(self.product_color, expected_data)

    def test_deserialization(self):
        expected_validated_data = {
            'display_color_name': self.data['display_color_name'],
            'color': self.product_color.color,
            'options': [
                {
                    'size': option.size,
                    'price_difference': option.price_difference
                }for option in self.options
            ],
            'image_url': validate_url(self.data['image_url']),
        }

        self._test_deserialzation(self.data, expected_validated_data)

    def test_default_display_color_name(self):
        self.data['display_color_name'] = None
        serializer = self._get_serializer_after_validation(data=self.data)

        self.assertEqual(
            serializer.validated_data['display_color_name'], 
            serializer.validated_data['color'].name
        )

    def test_validated_image_url_value(self):
        serializer = self._get_serializer_after_validation(data=self.data)

        self.assertEqual(
            serializer.validated_data['image_url'],
            validate_url(self.data['image_url'])
        )

    def test_raise_valid_error_update_color_data(self):
        color = ColorFactory()
        self.data['id'] = self.product_color.id
        self.data['color'] = color.id

        serializer = self._get_serializer(self.product_color, data=self.data, partial=True)
        expected_message = 'Color data cannot be updated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_create_data_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)

        serializer = self._get_serializer(
            self.product_color, data=self.data, partial=True
        )
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_create_non_unique_size_in_partial(self):
        self.data['id'] = self.product_color.id
        new_option_data = {
            'size': self.options[1].size,
            'price_difference': 0,
        }
        self.data['options'] = [new_option_data]

        serializer = self._get_serializer(
            self.product_color, data=self.data, partial=True
        )
        expected_message = 'The option with the size already exists.'

        self._test_serializer_raise_validation_error(serializer, expected_message)


class ProductColorListSerializerTestCase(ListSerializerTestCase):
    _serializer_class = ProductColorSerializer
    batch_size = 3

    @classmethod
    def setUpTestData(cls):
        cls.length_upper_limit = cls.get_list_serializer_class().length_upper_limit

        cls.product = ProductFactory()
        cls.product_colors = ProductColorFactory.create_batch(
            size=cls.batch_size, product=cls.product, display_color_name=None
        )
        for product_color in cls.product_colors:
            OptionFactory.create_batch(size=cls.batch_size, product_color=product_color)

        cls.update_data = [
            {
                'id': product_color.id,
                'display_color_name': product_color.display_color_name,
                'color': product_color.color.id,
                'options': [
                    {
                        'id': option.id,
                        'size': option.size, 
                        'price_difference': option.price_difference,
                    }for option in product_color.options.all()
                ],
                'image_url': BASE_IMAGE_URL + product_color.image_url,
            }for product_color in cls.product_colors
        ]

        cls.create_data = copy.deepcopy(cls.update_data)
        for data in cls.create_data:
            data.pop('id')

    def test_raise_valid_error_input_data_length_more_than_upper_limit_in_create(self):
        product_colors = ProductColorFactory.create_batch(size=self.length_upper_limit+1)
        for product_color in product_colors:
            OptionFactory.create_batch(size=self.batch_size, product_color=product_color)

        data = [
            {
                'display_color_name': product_color.display_color_name,
                'color': product_color.color.id,
                'options': [
                    {
                        'id': option.id,
                        'size': option.size, 
                        'price_difference': option.price_difference,
                    }for option in product_color.options.all()
                ],
                'image_url': BASE_IMAGE_URL + product_color.image_url,
            }for product_color in product_colors
        ]

        serializer = self._get_serializer(data=data)
        expected_message = 'The product cannot have more than ten colors.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_input_data_length_more_than_upper_limit_in_update(self):
        product = ProductFactory()
        product_colors = ProductColorFactory.create_batch(
            size=self.length_upper_limit+1, product=product, display_color_name=None
        )
        for product_color in product_colors:
            OptionFactory.create_batch(size=self.batch_size, product_color=product_color)

        data = [
            {
                'id': product_color.id,
                'display_color_name': product_color.display_color_name,
                'color': product_color.color.id,
                'options': [
                    {
                        'id': option.id,
                        'size': option.size, 
                        'price_difference': option.price_difference,
                    }for option in product_color.options.all()
                ],
                'image_url': BASE_IMAGE_URL + product_color.image_url,
            }for product_color in product_colors
        ]

        serializer = ProductWriteSerializer(product, data={'colors': data})
        expected_message = 'The product cannot have more than ten colors.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_input_data_length_is_zero(self):
        data = [
            {'id': product_color.id}
            for product_color in self.product_colors
        ]

        serializer = ProductWriteSerializer(
            self.product, data={'colors': data}, partial=True
        )
        expected_message = 'The product must have at least one color.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_display_color_name_duplicated_in_create(self):
        index = random.choice(range(1, len(self.create_data)))
        self.create_data[index]['display_color_name'] = self.create_data[0]['display_color_name']

        serializer = self._get_serializer(data=self.create_data)
        expected_message = 'display_color_name is duplicated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_display_color_name_duplicated_in_update(self):
        index = random.choice(range(1, len(self.update_data)))
        self.update_data[index]['display_color_name'] = self.update_data[0]['display_color_name']

        serializer = ProductWriteSerializer(
            self.product, data={'colors': self.update_data}, partial=True
        )
        expected_message = 'display_color_name is duplicated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_non_unique_display_color_name_in_update_data(self):
        data = [
            {
                'id': self.product_colors[0].id,
                'display_color_name': self.product_colors[1].display_color_name
            }
        ]

        serializer = ProductWriteSerializer(
            self.product, data={'colors': data}, partial=True
        )
        expected_message = 'The product with the display_color_name already exists.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_non_unique_display_color_name_in_create_data(self):
        data = [self.create_data[0]]

        serializer = ProductWriteSerializer(
            self.product, data = {'colors': data}, partial=True
        )
        expected_message = 'The product with the display_color_name already exists.'
        self._test_serializer_raise_validation_error(serializer, expected_message)