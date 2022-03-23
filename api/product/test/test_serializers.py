import random, copy

from django.test import tag
from django.db.models.query import Prefetch
from django.forms import model_to_dict

from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL, datetime_to_iso
from common.serializers import is_delete_data
from common.test.test_cases import SerializerTestCase, ListSerializerTestCase
from user.test.factory import WholesalerFactory
from ..validators import validate_url
from ..serializers import (
    ProductMaterialSerializer, SubCategorySerializer, MainCategorySerializer, ColorSerializer, SizeSerializer, LaundryInformationSerializer, 
    ThicknessSerializer, SeeThroughSerializer, ProductColorSerializer, FlexibilitySerializer, AgeSerializer, StyleSerializer, MaterialSerializer, 
    ProductImagesSerializer, OptionSerializer, ProductSerializer, ProductReadSerializer, ProductWriteSerializer, TagSerializer, ThemeSerializer,
)
from ..models import (
    Product, ProductColor, SubCategory, Style, Age, Tag, LaundryInformation, SeeThrough, Flexibility, Color, Thickness, Option, ProductMaterial,
    Theme,
)
from .factory import (
    ProductColorFactory, ProductFactory, SubCategoryFactory, MainCategoryFactory, ColorFactory, SizeFactory, LaundryInformationFactory, 
    TagFactory, ThemeFactory, ThicknessFactory, SeeThroughFactory, FlexibilityFactory, AgeFactory, StyleFactory, MaterialFactory, ProductImagesFactory,
    ProductMaterialFactory, OptionFactory, ThemeFactory, 
)

SAMPLE_PRODUCT_IMAGE_URL = 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_1.jpg'


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


class ThemeSerializerTestCase(SerializerTestCase):
    _serializer_class = ThemeSerializer

    def test_model_instance_serialization(self):
        theme = ThemeFactory()
        expected_data = {
            'id': theme.id,
            'name': theme.name,
        }

        self._test_model_instance_serialization(theme, expected_data)


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


class TagSerializerTestCase(SerializerTestCase):
    _serializer_class = TagSerializer

    def test_model_instance_serialization(self):
        tag = TagFactory()
        expected_data = {
            'id': tag.id,
            'name': tag.name,
        }

        self._test_model_instance_serialization(tag, expected_data)


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

    def test_raise_valid_error_image_url_not_starts_with_BASE_IMAGE_URL(self):
        image_url = 'https://omios.com/product/sample/product_1.jpg'

        self.__test_validate_image_url(
            image_url, expected_message='Enter a valid BASE_IMAGE_URL.'
        )

    def test_raise_valid_error_image_url_object_not_found(self):
        image_url = BASE_IMAGE_URL + 'product/sample/product_-999.jpg'

        self.__test_validate_image_url(
            image_url, expected_message='object not found.'
        )

    def test_raise_valid_error_create_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)

        serializer = self._get_serializer(self.product_images, data=self.data, partial=True)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_update_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        self.data['id'] = 100

        serializer = self._get_serializer(self.product_images, data=self.data, partial=True)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(serializer, expected_message)


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

    def __test_validate_create_raise_validation_error(self, data, expected_message):
        serializer = self._get_serializer(data=data)
        self._test_serializer_raise_validation_error(serializer, expected_message)

    def __test_validate_update_raise_validation_error(self, data, expected_message):
        serializer = ProductWriteSerializer(
            self.product, data={'images': data}, partial=True
        )

        self._test_serializer_raise_validation_error(serializer, expected_message)

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

    def test_raise_valid_error_sequences_not_startswith_one_in_create(self):
        sequences = range(5)
        self.__test_validate_create_wrong_sequence_ascending_order(sequences)

    def test_raise_valid_error_omitted_sequences_in_create(self):
        sequences = list(range(1, 6))
        sequences.pop(3)
        self.__test_validate_create_wrong_sequence_ascending_order(sequences)

    def test_raise_valid_error_does_not_pass_all_image_data_in_update(self):
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

    def test_raise_valid_error_does_not_pass_exact_image_data_in_update(self):
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

    def test_raise_valid_error_update_data_length_more_than_upper_limit(self):
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

    def test_raise_valid_error_data_length_is_zero(self):
        data = [
            {'id': product_image.id} 
            for product_image in self.product_images
        ]
        expected_message = 'The product must have at least one image.'

        self.__test_validate_update_raise_validation_error(data, expected_message)

    def test_raise_valid_error_sequences_not_startswith_one_in_update(self):
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

    def test_raise_valid_error_omitted_sequences_in_update(self):
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

    def test_raise_valid_error_create_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)

        serializer = self._get_serializer(self.product_material, data=self.data, partial=True)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(serializer, expected_message)
        
    def test_raise_valid_error_update_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        self.data['id'] = 100

        serializer = self._get_serializer(self.product_material, data=self.data, partial=True)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(serializer, expected_message)


class ProductMaterialListSerializerTestCase(ListSerializerTestCase):
    _serializer_class = ProductMaterialSerializer
    materials_num = 2

    @classmethod
    def setUpTestData(cls):
        sum_of_mixing_rates = cls.get_list_serializer_class().sum_of_mixing_rates
        mixing_rate = sum_of_mixing_rates / cls.materials_num

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

    def __test_raise_valid_error_in_create(self, data, expected_message):
        serializer = self._get_serializer(data=data)

        self._test_serializer_raise_validation_error(serializer, expected_message)
        
    def __test_raise_valid_error_in_update(self, data, expected_message):
        data = self.__get_update_data(data)
        serializer = ProductWriteSerializer(
            self.product, data=data, partial=True
        )

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_valid_error_total_mixing_rates_does_not_match_criteria_in_create(self):
        data = self.create_data
        data[0]['mixing_rate'] += 10

        expected_message = 'The total of material mixing rates must be 100.'

        self.__test_raise_valid_error_in_create(data, expected_message)

    def test_raise_valid_error_duplicated_material_name_in_create(self):
        data = self.create_data
        data[-1]['material'] = data[0]['material']

        expected_message = 'Material is duplicated.'

        self.__test_raise_valid_error_in_create(data, expected_message)

    def test_raise_valid_error_does_not_pass_all_material_data_in_update(self):
        data = self.update_data
        data.pop(0)

        expected_message = 'You must contain all material data that the product has.'

        self.__test_raise_valid_error_in_update(data, expected_message)

    def test_raise_valid_error_does_not_pass_exact_material_data_in_update(self):
        data = self.update_data
        data[-1]['id'] += 1

        expected_message = 'You must contain all material data that the product has.'

        self.__test_raise_valid_error_in_update(data, expected_message)

    def test_raise_valid_error_total_mixing_rates_does_not_match_criteria_in_update(self):
        self.update_data[-1] = {'id': self.update_data[-1]['id']}
        data = self.create_data + self.update_data

        mixing_rate = self.list_serializer_class.sum_of_mixing_rates / len(data)
        for d in data:
            if not is_delete_data(d):
                d['mixing_rate'] = mixing_rate

        expected_message = 'The total of material mixing rates must be 100.'

        self.__test_raise_valid_error_in_update(data, expected_message)

    def test_raise_valid_error_duplicated_material_name_in_update(self):
        data = self.create_data + self.update_data

        mixing_rate = self.list_serializer_class.sum_of_mixing_rates / len(data)
        for d in data:
            d['mixing_rate'] = mixing_rate

        data[-1]['material'] = data[0]['material']

        expected_message = 'Material is duplicated.'

        self.__test_raise_valid_error_in_update(data, expected_message)


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
                'size': SizeFactory().id,
                'price_difference': random.randint(0, cls.product_color.product.price * 0.2)
            }
            for _ in range(cls.options_num)
        ]

    def test_raise_validation_error_duplicated_size_data_in_create(self):
        data = self.create_data
        data[-1]['size'] = data[0]['size']

        serializer = self._get_serializer(data=data)
        expected_message = 'size is duplicated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_raise_validation_error_duplicated_size_data_in_update(self):
        self.create_data[-1]['size'] = self.create_data[0]['size']
        data = self.create_data
        data = {
            'colors': [
                {
                    'id': self.product_color.id,
                    'options': data,
                }
            ]
        }

        serializer = ProductWriteSerializer(self.product_color.product, data=data, partial=True)
        expected_message = 'size is duplicated.'

        self._test_serializer_raise_validation_error(serializer, expected_message)
    

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

    def test_raise_valid_error_non_unique_display_color_name_in_update_update_data(self):
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

    def test_raise_valid_error_non_unique_display_color_name_in_update_create_data(self):
        data = [self.create_data[0]]

        serializer = ProductWriteSerializer(
            self.product, data = {'colors': data}, partial=True
        )
        expected_message = 'The product with the display_color_name already exists.'
        self._test_serializer_raise_validation_error(serializer, expected_message)


class ProductSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductSerializer

    @classmethod
    def setUpTestData(cls):
        product = ProductFactory()
        ProductMaterialFactory(product=product)
        ProductColorFactory(product=product)
        ProductImagesFactory(product=product)

        cls.product_id = product.id

    def test_sort_dictionary_by_field_name(self):
        fields = list(self._get_serializer().get_fields().keys())
        random.shuffle(fields)

        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.product_id)
        serializer = self._get_serializer(product, context={'field_order': fields})

        self.assertListEqual(list(serializer.data.keys()), fields)


class ProductReadSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductReadSerializer

    @classmethod
    def setUpTestData(cls):
        cls.products = ProductFactory.create_batch(size=3)
        for product in cls.products:
            ProductMaterialFactory(product=product)
            ProductColorFactory(product=product)
            ProductImagesFactory.create_batch(size=3, product=product)
            laundry_informations = LaundryInformationFactory.create_batch(size=3)
            tags = TagFactory.create_batch(size=3)
            product.laundry_informations.add(*laundry_informations)
            product.tags.add(*tags)

    def __get_expected_data(self, product):
        expected_data = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'main_category': MainCategorySerializer(
                product.sub_category.main_category, allow_fields=('id', 'name')
                ).data,
            'sub_category': SubCategorySerializer(product.sub_category).data,
            'style': product.style.name,
            'age': product.age.name,
            'tags': [tag.name for tag in product.tags.all()] ,
            'materials': ProductMaterialSerializer(product.materials.all(), many=True).data,
            'laundry_informations': [info.name for info in product.laundry_informations.all()],
            'thickness': product.thickness.name,
            'see_through': product.see_through.name,
            'flexibility': product.flexibility.name,
            'lining': product.lining,
            'images': ProductImagesSerializer(product.images.all(), many=True).data,
            'colors': ProductColorSerializer(product.colors.all(), many=True).data,
            'created': datetime_to_iso(product.created),
            'on_sale': product.on_sale,
            'code': product.code,
            'manufacturing_country': product.manufacturing_country,
            'theme': product.theme.name,
        }

        return expected_data

    def test_model_instance_serialization_detail(self):
        expected_data = self.__get_expected_data(self.products[0])

        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.products[0].id)

        self._test_model_instance_serialization(product, expected_data, context={'detail': True})

    def test_model_instance_serialization_list(self):
        expected_data = [
            self.__get_expected_data(product)
            for product in self.products
        ]
        for data in expected_data:
            data['main_image'] = data['images'][0]['image_url']

        prefetch_images = Prefetch('images', to_attr='related_images')
        id_list = [product.id for product in self.products]
        product = Product.objects.prefetch_related(prefetch_images).filter(id__in=id_list)
        
        serializer = self._get_serializer(product, many=True, context={'detail': False})

        self.assertListEqual(serializer.data, expected_data)

    def test_default_image_detail(self):
        product = ProductFactory()
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=product.id)
        serializer = self._get_serializer(
            product, allow_fields=('id', 'images'), context={'detail': True}
        )
        expected_data = {
            'id': product.id,
            'images': [DEFAULT_IMAGE_URL],
        }

        self.assertDictEqual(serializer.data, expected_data)

    def test_default_image_list(self):
        products = ProductFactory.create_batch(size=3)
        id_list = [product.id for product in products]
        prefetch_images = Prefetch('images', to_attr='related_images')
        products = Product.objects.prefetch_related(prefetch_images).filter(id__in=id_list)
        serializer = self._get_serializer(
            products, allow_fields=('id',), many=True, context={'detail': False}
        )
        expected_data = [
            {
                'id': product.id,
                'main_image': DEFAULT_IMAGE_URL,
            }
            for product in products
        ]

        self.assertListEqual(serializer.data, expected_data)


class ProductWriteSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductWriteSerializer

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        for i in range(4):
            ProductMaterialFactory(product=cls.product, mixing_rate=25)

        product_colors = ProductColorFactory.create_batch(size=3, product=cls.product)
        for product_color in product_colors:
            OptionFactory.create_batch(size=3, product_color=product_color)

        for i in range(3):
            ProductImagesFactory(product=cls.product, sequence=i+1)

        laundry_informations = LaundryInformationFactory.create_batch(size=3)
        tags = TagFactory.create_batch(size=3)
        cls.product.laundry_informations.add(*laundry_informations)
        cls.product.tags.add(*tags)

    def __get_input_data(self):
        product = ProductFactory()
        tag_id_list = [tag.id for tag in TagFactory.create_batch(size=3)]
        tag_id_list.sort()
        laundry_information_id_list = [
            laundry_information.id for laundry_information in LaundryInformationFactory.create_batch(size=3)
        ]
        laundry_information_id_list.sort()
        color_id_list = [color.id for color in ColorFactory.create_batch(size=2)]

        data = {
            'name': 'name',
            'price': 50000,
            'sub_category': product.sub_category_id,
            'style': product.style_id,
            'age': product.age_id,
            'tags': tag_id_list,
            'materials': [
                {
                    'material': '가죽',
                    'mixing_rate': 80,
                },
                {
                    'material': '면', 
                    'mixing_rate': 20,
                },
            ],
            'laundry_informations': laundry_information_id_list,
            'thickness': product.thickness_id,
            'see_through': product.see_through_id,
            'flexibility': product.flexibility_id,
            'lining': True,
            'manufacturing_country': product.manufacturing_country,
            'theme': product.theme_id,
            'images': [
                {
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_11.jpg',
                    'sequence': 1
                },
                {
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_12.jpg',
                    'sequence': 2
                },
                {
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_13.jpg',
                    'sequence': 3
                }
            ],
            'colors': [
                {
                    'color': color_id_list[0],
                    'display_color_name': '다크',
                    'options': [
                        {
                            'size': 'Free',
                            'price_difference': 0
                        },
                        {
                            'size': 'S',
                            'price_difference': 0
                        }
                    ],
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_21.jpg'
                },
                {
                    'color': color_id_list[1],
                    'display_color_name': None,
                    'options': [
                        {
                            'size': 'Free',
                            'price_difference': 0
                        },
                        {
                            'size': 'S',
                            'price_difference': 2000
                        }
                    ],
                    'image_url': 'https://deepy.s3.ap-northeast-2.amazonaws.com/media/product/sample/product_22.jpg'
                }
            ]
        }

        return data

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product.id,
            'name': self.product.name,
            'price': self.product.price,
            'sub_category': self.product.sub_category_id,
            'style': self.product.style_id,
            'age': self.product.age_id,
            'tags': [tag.id for tag in self.product.tags.all()] ,
            'materials': ProductMaterialSerializer(self.product.materials.all(), many=True).data,
            'laundry_informations': [info.id for info in self.product.laundry_informations.all()],
            'thickness': self.product.thickness_id,
            'see_through': self.product.see_through_id,
            'flexibility': self.product.flexibility_id,
            'lining': self.product.lining,
            'manufacturing_country': self.product.manufacturing_country,
            'theme': self.product.theme_id,
            'images': ProductImagesSerializer(self.product.images.all(), many=True).data,
            'colors': ProductColorSerializer(self.product.colors.all(), many=True).data
        }
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.product.id)

        self._test_model_instance_serialization(product, expected_data)

    def test_deserialzation(self):
        data = self.__get_input_data()

        material_serializer = ProductMaterialSerializer(data=data['materials'], many=True)
        material_serializer.is_valid(raise_exception=True)

        image_serializer = ProductImagesSerializer(data=data['images'], many=True)
        image_serializer.is_valid(raise_exception=True)

        color_serializer = ProductColorSerializer(data=data['colors'], many=True)
        color_serializer.is_valid(raise_exception=True)

        expected_validated_data = {
            'name': data['name'],
            'price': data['price'],
            'sub_category': SubCategory.objects.get(id=data['sub_category']),
            'style': Style.objects.get(id=data['style']),
            'age': Age.objects.get(id=data['age']),
            'tags': list(Tag.objects.filter(id__in=data['tags'])),
            'materials': material_serializer.validated_data,
            'laundry_informations': list(LaundryInformation.objects.filter(id__in=data['laundry_informations'])),
            'thickness': Thickness.objects.get(id=data['thickness']),
            'see_through': SeeThrough.objects.get(id=data['see_through']),
            'flexibility': Flexibility.objects.get(id=data['flexibility']),
            'lining': data['lining'],
            'manufacturing_country': data['manufacturing_country'],
            'theme': Theme.objects.get(id=data['theme']),
            'related_images': image_serializer.validated_data,
            'colors': color_serializer.validated_data,
        }

        self._test_deserialzation(data, expected_validated_data)

    def test_raise_valid_error_price_difference_exceed_upper_limit(self):
        upper_limit_ratio = self._serializer_class.price_difference_upper_limit_ratio
        data = self.__get_input_data()
        option_data = data['colors'][0]['options']
        option_data[0]['price_difference'] = data['price'] *(1 +(upper_limit_ratio+0.1))

        serializer = self._get_serializer(data=data)
        expected_message = \
            'The option price difference must be less than {0}% of the product price.'.format(upper_limit_ratio * 100)

        self._test_serializer_raise_validation_error(serializer, expected_message)

    def test_create(self):
        data = self.__get_input_data()
        serializer = self._get_serializer_after_validation(
            data=data, context={'wholesaler': WholesalerFactory()}
        )
        product = serializer.save()

        self.assertEqual(product.name, data['name'])
        self.assertEqual(product.price, data['price'])
        self.assertEqual(product.sub_category_id, data['sub_category'])
        self.assertEqual(product.style_id, data['style'])
        self.assertEqual(product.age_id, data['age'])
        self.assertEqual(product.thickness_id, data['thickness'])
        self.assertEqual(product.see_through_id, data['see_through'])
        self.assertEqual(product.flexibility_id, data['flexibility'])
        self.assertEqual(product.lining, data['lining'])
        self.assertEqual(product.manufacturing_country, data['manufacturing_country'])
        self.assertEqual(product.theme_id, data['theme'])
        self.assertListEqual(
            list(product.tags.all().order_by('id').values_list('id', flat=True)),
            data['tags']
        )
        self.assertListEqual(
            list(
                product.materials.all().order_by('id').values('material', 'mixing_rate')
            ),
            data['materials']
        )
        self.assertListEqual(
            list(
                product.laundry_informations.all().order_by('id').values_list('id', flat=True)
            ),
            data['laundry_informations']
        )
        self.assertListEqual(
            list(product.images.all().order_by('id').values('image_url', 'sequence')),
            [
                {
                    'image_url': validate_url(data['image_url']),
                    'sequence': data['sequence'],
                } for data in data['images']
            ]
        )
        self.assertListEqual(
            list(
                product.colors.all().order_by('id').values('color', 'display_color_name', 'image_url')
            ),
            [
                {
                    'color': data['color'],
                    'display_color_name': data['display_color_name'] 
                        if data['display_color_name'] is not None 
                        else Color.objects.get(id=data['color']).name,
                    'image_url': validate_url(data['image_url']),
                }for data in data['colors']
            ]
        )
        self.assertListEqual(
            list(Option.objects.filter(product_color__product=product).order_by('id')
            .values('size', 'price_difference')),
            [
                option_data for color_data in data['colors'] for option_data in color_data['options']
            ]
        )

    def test_update_product_attribute(self):
        update_data = {}
        update_data['name'] = self.product.name + '_update'
        update_data['price'] = self.product.price + 10000
        update_data['sub_category'] = SubCategoryFactory().id
        update_data['style'] = StyleFactory().id
        update_data['age'] = AgeFactory().id
        update_data['thickness'] = ThicknessFactory().id
        update_data['see_through'] = SeeThroughFactory().id
        update_data['flexibility'] = FlexibilityFactory().id
        update_data['lining'] = not self.product.lining
        update_data['manufacturing_country'] = self.product.manufacturing_country + '_update'
        update_data['theme'] = ThemeFactory().id
        serializer = self._get_serializer_after_validation(
            self.product, data=update_data, partial=True
        )
        product = serializer.save()

        self.assertEqual(product.name, update_data['name'])
        self.assertEqual(product.price, update_data['price'])
        self.assertEqual(product.sub_category_id, update_data['sub_category'])
        self.assertEqual(product.style_id, update_data['style'])
        self.assertEqual(product.age_id, update_data['age'])
        self.assertEqual(product.thickness_id, update_data['thickness'])
        self.assertEqual(product.see_through_id, update_data['see_through'])
        self.assertEqual(product.flexibility_id, update_data['flexibility'])
        self.assertEqual(product.lining, update_data['lining'])
        self.assertEqual(product.manufacturing_country, update_data['manufacturing_country'])
        self.assertEqual(product.theme_id, update_data['theme'])

    def test_update_id_only_m2m_fields(self):
        tags = TagFactory.create_batch(size=2)
        remaining_tags = random.sample(
            list(self.product.tags.all().values_list('id', flat=True)), 
            2
        )
        tag_id_list = [tag.id for tag in tags] + remaining_tags
        tag_id_list.sort()

        update_data = {'tags': tag_id_list}
        serializer = self._get_serializer_after_validation(
            self.product, data=update_data, partial=True
        )
        product = serializer.save()

        self.assertListEqual(
            list(product.tags.all().order_by('id').values_list('id', flat=True)),
            tag_id_list
        )

    def test_update_many_to_one_fields(self):
        materials = self.product.materials.all()
        delete_materials = materials[:1]
        update_materials = materials[1:]
        create_data = [
            {
                'material': 'mat_create',
            }
        ]
        delete_data = list(delete_materials.values('id'))
        update_data = [
            {
                'id': material.id,
                'material': material.material + '_update',
                'mixing_rate': material.mixing_rate,
            }
            for material in update_materials
        ]
        for data in create_data:
            data['mixing_rate'] = 100 // len(create_data + update_data)
        for data in update_data:
            data['mixing_rate'] = 100 // len(create_data + update_data)

        data = {
            'materials': create_data + update_data + delete_data,
        }
        
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        product = serializer.save()

        deleted_id_list = [data['id'] for data in delete_data]
        updated_id_list = [data['id'] for data in update_data]

        self.assertTrue(not ProductMaterial.objects.filter(id__in=deleted_id_list).exists())
        self.assertListEqual(
            list(ProductMaterial.objects.filter(product=product).exclude(id__in=updated_id_list)
            .values('material', 'mixing_rate')),
            create_data
        )
        self.assertListEqual(
            list(ProductMaterial.objects.filter(id__in=updated_id_list)
            .values('id', 'material', 'mixing_rate')),
            update_data
        )

    def test_delete_product_colors_in_update(self):
        delete_product_color_id = self.product.colors.latest('id').id
        data = {
            'colors': [
                {'id': delete_product_color_id}
            ]
        }
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()
        self.assertTrue(
            not ProductMaterial.objects.filter(id=delete_product_color_id).exists()
        )

    def test_create_product_colors_in_update(self):
        existing_color_id_list = list(self.product.colors.all().values_list('id', flat=True))
        create_color_data = self.__get_input_data()['colors']
        create_option_data = [
            option_data for color_data in create_color_data for option_data in color_data['options']
        ]
        data = {'colors': create_color_data}
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()

        self.assertListEqual(
            list(
                ProductColor.objects.filter(product=self.product).exclude(id__in=existing_color_id_list)
                .order_by('id').values('color', 'display_color_name', 'image_url')
            ),
            [
                {
                    'color': d['color'],
                    'display_color_name': d['display_color_name']
                        if d['display_color_name'] is not None
                        else Color.objects.get(id=d['color']).name,
                    'image_url': validate_url(d['image_url']),
                }for d in data['colors']
            ]
        )
        self.assertListEqual(
            list(
                Option.objects.filter(product_color__product=self.product)
                .exclude(product_color_id__in=existing_color_id_list).order_by('id')
                .values('size', 'price_difference')
            ),
            [
                {
                    'size': data['size'],
                    'price_difference': data['price_difference'],
                }for data in create_option_data
            ]
        )

    def test_update_product_colors_except_options(self):
        update_color_obj = self.product.colors.latest('id')
        update_data = {
            'id': update_color_obj.id,
            'display_color_name': '_updated',
            'image_url': SAMPLE_PRODUCT_IMAGE_URL,
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()

        updated_color_obj = self.product.colors.get(id=update_color_obj.id)
        expected_dict = update_data
        expected_dict['image_url'] = validate_url(expected_dict['image_url'])

        self.assertDictEqual(
            model_to_dict(updated_color_obj, fields=('id', 'display_color_name', 'image_url')),
            expected_dict
        )

    def test_create_option_in_update(self):
        update_color_obj = self.product.colors.latest('id')
        existing_option_id_list = list(update_color_obj.options.values_list('id', flat=True))
        update_data = {
            'id': update_color_obj.id,
            'options': [
                {
                    'size': 'Free',
                    'price_difference': 0
                }
            ]
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()

        self.assertListEqual(
            list(
                Option.objects.filter(product_color=update_color_obj).exclude(id__in=existing_option_id_list)
                .order_by('id').values('size', 'price_difference')
            ),
            update_data['options']
        )

    def test_update_option(self):
        update_color_obj = self.product.colors.latest('id')
        update_option_obj = update_color_obj.options.latest('id')
        update_data = {
            'id': update_color_obj.id,
            'options': [
                {
                    'id': update_option_obj.id,
                    'price_difference': update_option_obj.price_difference + 500
                }
            ]
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()
        updated_option_obj = Option.objects.get(id=update_option_obj.id)
        
        self.assertDictEqual(
            model_to_dict(updated_option_obj, fields=('id', 'price_difference')),
            update_data['options'][0]
        )

    @tag('exclude')
    def test_delete_option(self):
        update_color_obj = self.product.colors.latest('id')
        delete_option_id = update_color_obj.options.latest('id').id
        update_data = {
            'id': update_color_obj.id,
            'options': [
                {
                    'id': delete_option_id
                }
            ]
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()

        self.assertTrue(not Option.objects.get(id=delete_option_id).on_sale)
