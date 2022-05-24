import random, copy

from django.db.models.query import Prefetch
from django.db.models import Count
from django.forms import model_to_dict

from rest_framework.exceptions import ValidationError

from common.models import TemporaryImage
from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL, datetime_to_iso
from common.test.test_cases import SerializerTestCase, ListSerializerTestCase
from user.test.factories import WholesalerFactory, ShopperFactory
from user.models import ProductLike
from .factories import (
    ProductColorFactory, ProductFactory, SubCategoryFactory, MainCategoryFactory, ColorFactory, SizeFactory, LaundryInformationFactory, 
    TagFactory, ThemeFactory, ThicknessFactory, SeeThroughFactory, FlexibilityFactory, AgeFactory, StyleFactory, MaterialFactory, ProductImageFactory,
    ProductMaterialFactory, OptionFactory, ThemeFactory, ProductQuestionAnswerFactory, ProductQuestionAnswerClassificationFactory,
)
from ..serializers import (
    ProductMaterialSerializer, SubCategorySerializer, MainCategorySerializer, ColorSerializer, SizeSerializer, LaundryInformationSerializer, 
    ThicknessSerializer, SeeThroughSerializer, ProductColorSerializer, FlexibilitySerializer, AgeSerializer, StyleSerializer, MaterialSerializer, 
    ProductImageSerializer, OptionSerializer, ProductSerializer, ProductReadSerializer, ProductWriteSerializer, TagSerializer, ThemeSerializer,
    ProductQuestionAnswerSerializer, ProductQuestionAnswerClassificationSerializer, OptionInOrderItemSerializer,
    PRODUCT_IMAGE_MAX_LENGTH, PRODUCT_COLOR_MAX_LENGTH,
)
from ..models import Product, ProductColor, Color, Option, ProductMaterial, ProductQuestionAnswer, ProductImage


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
            'sub_categories': [
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


class ProductImageSerializerTestCase(SerializerTestCase):
    fixtures = ['temporary_image']
    _serializer_class = ProductImageSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__image_url = TemporaryImage.objects.first().image_url
        cls.__product_image = ProductImageFactory()
        cls._data = {
            'image_url': BASE_IMAGE_URL + cls.__image_url,
            'sequence': 1,
        }

    def test_model_instance_serialization(self):

        expected_data = {
            'id': self.__product_image.id,
            'image_url': BASE_IMAGE_URL + self.__product_image.image_url,
            'sequence': self.__product_image.sequence,
        }

        self._test_model_instance_serialization(self.__product_image, expected_data)

    def _test_validated_data(self):
        expected_validated_data = {
            'image_url': self.__image_url,
            'sequence': self._data['sequence']
        }

        self._test_validated_data(expected_validated_data, data=self._data)

    def test_raise_validation_error_create_data_does_not_include_all_required_field_in_update(self):
        key = random.choice(list(self._data.keys()))
        self._data.pop(key)

        expected_message = '{0} field is required.'.format(key)
        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_image, data=self._data, partial=True
        )

    def test_raise_validation_error_update_image_url(self):
        data = {
            'id': self.__product_image.id,
            'image_url': BASE_IMAGE_URL + TemporaryImage.objects.last().image_url,
            'sequence': 1,
        }

        expected_message = 'Image url data cannot be updated.'
        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_image, data=data, partial=True
        )


class ProductImageListSerializerTestCase(ListSerializerTestCase):
    fixtures = ['temporary_image']
    _child_serializer_class = ProductImageSerializer
    __batch_size = 2

    @classmethod
    def setUpTestData(cls):
        cls.__temporary_images = TemporaryImage.objects.all().values_list('image_url', flat=True)
        cls.__data = [
            {
                'image_url': BASE_IMAGE_URL + cls.__temporary_images[i],
                'sequence': i+1,
            } for i in range(cls.__batch_size)
        ]
        cls.__product = ProductFactory()
        cls.__images = ProductImageFactory.create_batch(size=cls.__batch_size, product=cls.__product)

    def test_create(self):
        serializer = self._get_serializer()
        serializer.create(self.__data, self.__product)
        
        exclude_id_list = [image.id for image in self.__images]
        created_images = self.__product.images.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{'image_url': image.image_url, 'sequence': image.sequence} for image in created_images],
            [{'image_url': data['image_url'], 'sequence': data['sequence']} for data in self.__data]
        )

    def test_update_create_data(self):
        serializer = self._get_serializer()
        serializer.update(self.__data, self.__product)

        exclude_id_list = [image.id for image in self.__images]
        created_images = self.__product.images.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{'image_url': image.image_url, 'sequence': image.sequence} for image in created_images],
            [{'image_url': data['image_url'], 'sequence': data['sequence']} for data in self.__data]
        )

    def test_update_update_data(self):
        updating_image = self.__images[0]
        data = [{
            'id': updating_image.id,
            'sequence': updating_image.sequence + 1,
        }]

        serializer = self._get_serializer()
        serializer.update(data, self.__product)

        updated_image = self.__product.images.get(id=updating_image.id)

        self.assertListEqual(
            data, [model_to_dict(updated_image, fields=['id', 'sequence'])]
        )

    def test_update_delete_data(self):
        delete_id = self.__images[-1].id
        data = [{'id': delete_id}]

        serializer = self._get_serializer()
        serializer.update(data, self.__product)

        self.assertTrue(not self.__product.images.filter(id=delete_id).exists())

    def test_validate_image_number_in_create(self):
        data = [{} for _ in range(PRODUCT_COLOR_MAX_LENGTH + 1)]

        self.assertRaisesMessage(
            ValidationError,
            'The product cannot have more than ten images.',
            self._get_serializer().validate,
            data
        )

    def test_validate_image_number_in_update_number_more_than_max(self):
        self.__data += [
            {
                'image_url': BASE_IMAGE_URL + self.__temporary_images[i],
                'sequence': i+1,
            } for i in range(len(self.__images), PRODUCT_IMAGE_MAX_LENGTH + len(self.__images) + 1)
        ]
        self.__data += [{'id': image.id} for image in self.__images]

        self.assertRaisesMessage(
            ValidationError,
            'The product cannot have more than ten images.',
            self._get_serializer(instance=self.__product, partial=True).validate,
            self.__data
        )

    def test_validate_image_number_in_update_number_delete_all_images(self):
        data = [{'id': image.id} for image in self.__images]

        self.assertRaisesMessage(
            ValidationError,
            'The product must have at least one image.',
            self._get_serializer(instance=self.__product, partial=True).validate,
            data
        )

    def test_validate_sequence_sequences_not_startswith_one_in_create(self):
        for data in self.__data:
            data['sequence'] += 1

        self.assertRaisesMessage(
            ValidationError,
            'The sequence of the images must be ascending from 1 to n.',
            self._get_serializer(instance=self.__product, partial=True).validate,
            self.__data
        )

    def test_raise_validation_error_duplicated_sequences_in_create(self):
        self.__data[0]['sequence'] = self.__data[-1]['sequence']

        self.assertRaisesMessage(
            ValidationError,
            'The sequence of the images must be ascending from 1 to n.',
            self._get_serializer(instance=self.__product).validate,
            self.__data
        )

    def test_raise_validation_error_omitted_sequences_in_create(self):
        self.__data[-1]['sequence'] += 1

        self.assertRaisesMessage(
            ValidationError,
            'The sequence of the images must be ascending from 1 to n.',
            self._get_serializer(instance=self.__product).validate,
            self.__data
        )

    def test_raise_validation_error_duplicated_sequences_in_update(self):
        data = [{
            'id': self.__images[0].id,
            'sequence': self.__images[-1].sequence + 1,
        }]

        self.assertRaisesMessage(
            ValidationError,
            'The sequence of the images must be ascending from 1 to n.',
            self._get_serializer(instance=self.__product).validate,
            data
        )

    def test_raise_validation_error_duplicated_sequences_in_update(self):
        data = [{
                'image_url': BASE_IMAGE_URL + self.__temporary_images[0], 
                'sequence': self.__product.images.last().sequence,
            }]

        self.assertRaisesMessage(
            ValidationError,
            'The sequence of the images must be ascending from 1 to n.',
            self._get_serializer(instance=self.__product).validate,
            data
        )

    def test_raise_validation_error_omitted_sequences_in_update(self):
        data = [{
                'image_url': BASE_IMAGE_URL + self.__temporary_images[0], 
                'sequence': self.__product.images.last().sequence + 2,
            }]

        self.assertRaisesMessage(
            ValidationError,
            'The sequence of the images must be ascending from 1 to n.',
            self._get_serializer(instance=self.__product).validate,
            data
        )


class ProductMaterialSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductMaterialSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__product = ProductFactory()
        cls.__product_material = ProductMaterialFactory(product=cls.__product)
        cls.__data = {
            'material': '가죽',
            'mixing_rate': 100,
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.__product_material.id,
            'material': self.__product_material.material,
            'mixing_rate': self.__product_material.mixing_rate,
        }

        self._test_model_instance_serialization(self.__product_material, expected_data)

    def test_raise_validation_error_create_data_does_not_include_all_required_field_in_update(self):
        key = random.choice(list(self.__data.keys()))
        self.__data.pop(key)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_material, data=self.__data, partial=True
        )


class ProductMaterialListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = ProductMaterialSerializer
    __material_num = 2

    @classmethod
    def setUpTestData(cls):
        cls.__product = ProductFactory()
        cls.__materials = ProductMaterialFactory.create_batch(
            cls.__material_num, product=cls.__product, mixing_rate=50
        )
        cls.__create_data = [
            {
                'material': cls.__materials[i].material,
                'mixing_rate': 50,
            }for i in range(cls.__material_num)
        ]
        cls.__update_data = [
            {
                'id': cls.__materials[i].id,
                'material': cls.__materials[i].material,
                'mixing_rate': 50,
            }for i in range(cls.__material_num)
        ]

    def test_create(self):
        serializer = self._get_serializer()
        serializer.create(self.__create_data, self.__product)

        exclude_id_list = [material.id for material in self.__materials]
        created_materials = self.__product.materials.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{'material': material.material, 'mixing_rate': material.mixing_rate} for material in created_materials],
            [{'material': data['material'], 'mixing_rate': data['mixing_rate']} for data in self.__create_data]
        )

    def test_update_create_data(self):
        serializer = self._get_serializer()
        serializer.update(self.__create_data, self.__product)

        exclude_id_list = [material.id for material in self.__materials]
        created_materials = self.__product.materials.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{'material': material.material, 'mixing_rate': material.mixing_rate} for material in created_materials],
            [{'material': data['material'], 'mixing_rate': data['mixing_rate']} for data in self.__create_data]
        )

    def test_update_update_data(self):
        updating_material = self.__materials[0]
        data = [{
            'id': updating_material.id,
            'material': updating_material.material + 'update',
            'mixing_rate': updating_material.mixing_rate + 10,
        }]

        serializer = self._get_serializer()
        serializer.update(data, self.__product)

        updated_material = self.__product.materials.get(id=updating_material.id)

        self.assertListEqual(
            data,
            [model_to_dict(updated_material, fields=['id', 'material', 'mixing_rate'])]
        )

    def test_update_delete_data(self):
        delete_id = self.__materials[-1].id
        data = [{'id': delete_id}]

        serializer = self._get_serializer()
        serializer.update(data, self.__product)

        self.assertTrue(not self.__product.materials.filter(id=delete_id).exists())

    def test_validate_total_mixing_rates_in_create(self):
        self.__create_data[0]['mixing_rate'] += 10

        self.assertRaisesMessage(
            ValidationError,
            'The total of material mixing rates must be 100.',
            self._get_serializer().validate,
            self.__create_data
        )

    def test_validate_total_mixing_rates_in_update(self):
        self.__update_data[0] = {'id': self.__update_data[0]['id']}
        self.__update_data.pop(-1)
        self.__update_data.append({
            'material': 'material',
            'mixing_rate': 60,
        })

        self.assertRaisesMessage(
            ValidationError,
            'The total of material mixing rates must be 100.',
            self._get_serializer(instance=self.__product).validate,
            self.__update_data
        )

    def test_validate_material_is_duplicated(self):
        self.__create_data[0]['material'] = self.__create_data[-1]['material']

        self.assertRaisesMessage(
            ValidationError,
            'Material is duplicated.',
            self._get_serializer(instance=self.__product).validate,
            self.__create_data
        )

    def test_validate_material_name_uniqueness(self):
        data = [{
            'id': self.__materials[0].id,
            'mixing_rate': self.__materials[0].mixing_rate - 10,
        },
        {
            'material': self.__materials[0].material,
            'mixing_rate': 10,
        }]

        self.assertRaisesMessage(
            ValidationError,
            'The product with the material already exists.',
            self._get_serializer(instance=self.__product).validate,
            data
        )

    def test_delete_and_create_material_name(self):
        data = [
            {
                'material': self.__materials[0].material,
                'mixing_rate': self.__materials[0].mixing_rate,
            },
            {
                'id': self.__materials[0].id,
            }
        ]

        self.assertEqual(
            data, self._get_serializer(instance=self.__product).validate(data)
        )

    def test_exchange_material_name(self):
        material1 = self.__materials[0]
        material2 = self.__materials[1]
        data = [{
            'id': material1.id,
            'material': material2.material,
        },
        {
            'id': material2.id,
            'material': material1.material,
        }
        ]

        self.assertEqual(
            data,
            self._get_serializer(instance=self.__product).validate(data)
        )


class OptionSerializerTestCase(SerializerTestCase):
    _serializer_class = OptionSerializer

    @classmethod
    def setUpTestData(cls):
        size = SizeFactory()
        cls.__option = OptionFactory(size = size.name)
        cls.__data = {'size': 'Free'}

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.__option.id, 
            'size': self.__option.size,
            'on_sale': self.__option.on_sale,
        }

        self._test_model_instance_serialization(self.__option, expected_data)

    def test_raise_validation_error_update_size_data(self):
        self.__data['id'] = self.__option.id
        self.__data['size'] = self.__data['size'] + 'update'
        expected_message = 'Size data cannot be updated.'

        self._test_serializer_raise_validation_error(
            expected_message, self.__option, data=self.__data, partial=True
        )


class OptionListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = OptionSerializer
    __option_num = 3

    @classmethod
    def setUpTestData(cls):
        cls.__product_color = ProductColorFactory()
        cls.__options = OptionFactory.create_batch(size=cls.__option_num, product_color=cls.__product_color)
        cls.__data = [
            {'size': SizeFactory().name}
            for _ in range(cls.__option_num)
        ]

    def test_create(self):
        serializer = self._get_serializer()
        serializer.create(self.__data, self.__product_color)

        exclude_id_list = [option.id for option in self.__options]
        created_options = self.__product_color.options.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{'size': option.size} for option in created_options],
            [{'size': data['size']} for data in self.__data]
        )

    def test_update_create_data(self):
        serializer = self._get_serializer()
        serializer.update(self.__data, self.__product_color)

        exclude_id_list = [option.id for option in self.__options]
        created_options = self.__product_color.options.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{'size': option.size} for option in created_options],
            [{'size': data['size']} for data in self.__data]
        )

    def test_update_update_data(self):
        updating_option = self.__options[0]
        data = {
            'id': updating_option.id,
            'size': updating_option.size + 'update',
        }

        serializer = self._get_serializer()
        serializer.update([data], self.__product_color)

        updated_option = self.__product_color.options.get(id=updating_option.id)

        self.assertDictEqual(
            data,
            model_to_dict(updated_option, fields=['id', 'size'])
        )

    def test_update_delete_data(self):
        delete_id = self.__options[-1].id
        data = [{'id': delete_id}]

        serializer = self._get_serializer()
        serializer.update(data, self.__product_color)

        self.assertTrue(not self.__product_color.options.filter(id=delete_id, on_sale=True).exists())

    def test_raise_validation_error_duplicated_size_data_in_create(self):
        data = self.__data
        data[-1]['size'] = data[0]['size']
        expected_message = 'Size is duplicated.'

        self._test_serializer_raise_validation_error(expected_message, data=data)

    def test_raise_validation_error_duplicated_size_data_in_update(self):
        self.__data[-1]['size'] = self.__data[0]['size']
        data = self.__data
        expected_message = 'Size is duplicated.'

        self._test_serializer_raise_validation_error(
            expected_message, data=data, partial=True
        )


class OptionInOrderItemSerializerTestCase(SerializerTestCase):
    _serializer_class = OptionInOrderItemSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__option = OptionFactory()
        cls.__expected_data = {
            'id': cls.__option.id,
            'size': cls.__option.size,
            'display_color_name': cls.__option.product_color.display_color_name,
            'product_id': cls.__option.product_color.product.id,
            'product_name': cls.__option.product_color.product.name,
            'product_code': cls.__option.product_color.product.code,
        }

    def test_model_instance_serialization_with_image(self):
        img = ProductImageFactory(product=self.__option.product_color.product)
        self.__expected_data['product_image_url'] = BASE_IMAGE_URL + img.image_url

        self._test_model_instance_serialization(self.__option, self.__expected_data)

    def test_model_instance_serialization_without_image(self):
        self.__expected_data['product_image_url'] = DEFAULT_IMAGE_URL

        self._test_model_instance_serialization(self.__option, self.__expected_data)



class ProductColorSerializerTestCase(SerializerTestCase):
    fixtures = ['temporary_image']
    _serializer_class = ProductColorSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__product_color = ProductColorFactory()
        cls.__options = OptionFactory.create_batch(
            size=3, product_color=cls.__product_color
        )
        cls.data = {
            'display_color_name': 'deepblue',
            'color': cls.__product_color.color.id,
            'options': [
                {'size': option.size}
                for option in cls.__options
            ],
            'image_url': BASE_IMAGE_URL + TemporaryImage.objects.first().image_url,
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.__product_color.id,
            'display_color_name': self.__product_color.display_color_name,
            'color': self.__product_color.color.id,
            'options': OptionSerializer(self.__options, many=True).data,
            'image_url': BASE_IMAGE_URL + self.__product_color.image_url,
            'on_sale': self.__product_color.on_sale,
        }
        self._test_model_instance_serialization(self.__product_color, expected_data)

    def test_raise_validation_error_update_color_data(self):
        color = ColorFactory()
        self.data['id'] = self.__product_color.id
        self.data['color'] = color.id
        expected_message = 'Color data cannot be updated.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_color, data=self.data, partial=True
        )

    def test_raise_validation_error_create_data_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_color, data=self.data, partial=True
        )

    def test_raise_validation_error_update_non_unique_size_in_partial(self):
        self.data['id'] = self.__product_color.id
        new_option_data = {'size': self.__options[1].size}
        self.data['options'] = [new_option_data]
        expected_message = 'The option with the size already exists.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_color, data=self.data, partial=True
        )

    def test_raise_validation_error_delete_all_options(self):
        data = {
            'id': self.__product_color.id,
            'options': [
                {'id': option.id}
                for option in self.__options
            ]
        }
        expected_message = 'The product color must have at least one option.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product_color, data=data, partial=True
        )


class ProductColorListSerializerTestCase(ListSerializerTestCase):
    fixtures = ['temporary_image']
    _child_serializer_class = ProductColorSerializer
    __batch_size = 2

    @classmethod
    def setUpTestData(cls):
        cls.__color = ColorFactory()
        cls.__temporary_images = list(TemporaryImage.objects.all().values_list('image_url', flat=True))
        cls.__product = ProductFactory()
        cls.__product_colors = [
            ProductColorFactory(product=cls.__product, image_url=cls.__temporary_images[i], color=cls.__color)
            for i in range(cls.__batch_size)
        ]
        for product_color in cls.__product_colors:
            OptionFactory(product_color=product_color)

        cls.__data = [{
            'display_color_name': cls.__color.name,
            'color': cls.__color,
            'options': [{
                'size': 'size',
            }],
            'image_url': BASE_IMAGE_URL + cls.__temporary_images[0]
        }]

    def test_create(self):
        serializer = self._get_serializer()
        serializer.create(copy.deepcopy(self.__data), self.__product)

        exclude_id_list = [product_color.id for product_color in self.__product_colors]
        created_product_colors = self.__product.colors.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{
                'display_color_name': color.display_color_name,
                'color': color.color,
                'options': [{'size': option.size} for option in color.options.all()],
                'image_url': color.image_url,
            }for color in created_product_colors],
            self.__data
        )

    def test_update_create_data(self):
        serializer = self._get_serializer()
        serializer.update(copy.deepcopy(self.__data), self.__product)

        exclude_id_list = [product_color.id for product_color in self.__product_colors]
        created_product_colors = self.__product.colors.exclude(id__in=exclude_id_list)

        self.assertListEqual(
            [{
                'display_color_name': color.display_color_name,
                'color': color.color,
                'options': [{'size': option.size} for option in color.options.all()],
                'image_url': color.image_url,
            }for color in created_product_colors],
            self.__data
        )

    def test_update_update_data(self):
        updating_product_color = self.__product_colors[0]
        data = [{
            'id': updating_product_color.id,
            'display_color_name': updating_product_color.display_color_name + 'update',
            'color': ColorFactory(),
            'image_url': updating_product_color.image_url + 'update',
        }]

        serializer = self._get_serializer()
        serializer.update(data, self.__product)

        updated_product_color = self.__product.colors.get(id=updating_product_color.id)

        self.assertListEqual(
            [{
                'id': updated_product_color.id,
                'display_color_name': updated_product_color.display_color_name,
                'color': updated_product_color.color,
                'image_url': updated_product_color.image_url,
            }],
            data
        )

    def test_update_delete_data(self):
        delete_id = self.__product_colors[-1].id
        data = [{'id': delete_id}]

        serializer = self._get_serializer()
        serializer.update(data, self.__product)

        self.assertTrue(not self.__product.colors.filter(id=delete_id, on_sale=True).exists())

    def test_validate_color_length_in_create(self):
        data = [{} for _ in range(11)]

        self.assertRaisesMessage(
            ValidationError,
            'The product cannot have more than ten colors.',
            self._get_serializer().validate,
            data
        )

    def test_validate_color_length_in_update_more_than_max_length(self):
        create_data = [
            {
                'display_color_name': 'display_name{0}'.format(i),
                'color': self.__color.id,
                'options': [
                    {
                        'size': 'size{0}'.format(i),
                    }
                ],
                'image_url': BASE_IMAGE_URL + self.__temporary_images[i]
            }
            for i in range(PRODUCT_COLOR_MAX_LENGTH + 1)
        ]
        delete_data = list(self.__product.colors.all().values('id'))
        
        self.assertRaisesMessage(
            ValidationError,
            'The product cannot have more than ten colors.',
            self._get_serializer(instance=self.__product).validate,
            create_data + delete_data
        )

    def test_validate_color_length_in_update_delete_all_colors(self):
        data = list(self.__product.colors.all().values('id'))

        self.assertRaisesMessage(
            ValidationError,
            'The product must have at least one color.',
            self._get_serializer(instance=self.__product).validate,
            data
        )

    def test_validate_display_color_name_is_duplicated(self):
        data = [
            {'display_color_name': 'display'},
            {'display_color_name': 'display'},
            {'display_color_name': 'display_1'}
        ]

        self.assertRaisesMessage(
            ValidationError,
            'display_color_name is duplicated.',
            self._get_serializer().validate,
            data
        )

    def test_validate_display_color_name_uniqueness(self):
        data = [{
            'display_color_name': self.__product.colors.first().display_color_name,
            'color': self.__color.id,
            'options': [
                {
                    'size': 'size',
                }
            ],
            'image_url': BASE_IMAGE_URL + self.__temporary_images[0]
        }]

        self.assertRaisesMessage(
            ValidationError,
            'The product with the display_color_name already exists.',
            self._get_serializer(instance=self.__product).validate,
            data
        )

    def test_delete_and_create_display_color_name(self):
        data = [{
            'display_color_name': self.__product_colors[0].display_color_name,
            'color': self.__color.id,
            'options': [
                {
                    'size': 'size',
                }
            ],
            'image_url': BASE_IMAGE_URL + self.__temporary_images[0]
        },
        {
            'id': self.__product_colors[0].id,
        }]

        self.assertEqual(
            data, self._get_serializer(instance=self.__product).validate(data)
        )

    def test_exchange_display_color_name(self):
        color1 = self.__product_colors[0]
        color2 = self.__product_colors[1]
        data = [
            {
                'id': color1.id,
                'display_color_name': color2.display_color_name,
            },
            {
                'id': color2.id,
                'display_color_name': color1.display_color_name,
            },
        ]

        self.assertEqual(
            data, self._get_serializer(instance=self.__product).validate(data)
        )

    def test_create_display_color_name_on_sale_false(self):
        self.__product_colors[0].on_sale = False
        self.__product_colors[0].save()
        data = [{
            'id': self.__product_colors[1].id,
            'display_color_name': self.__product_colors[0].display_color_name,
        }]

        self.assertEqual(
            data, self._get_serializer(instance=self.__product).validate(data)
        )

class ProductSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__product = ProductFactory()

    def test_sort_dictionary_by_field_name(self):
        fields = list(self._get_serializer().get_fields().keys())
        random.shuffle(fields)

        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.__product.id)
        serializer = self._get_serializer(product, context={'field_order': fields})

        self.assertListEqual(list(serializer.data.keys()), fields)


class ProductReadSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductReadSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__product = ProductFactory()
        ProductMaterialFactory(product=cls.__product)
        ProductColorFactory(product=cls.__product)
        ProductImageFactory.create_batch(size=3, product=cls.__product)
        laundry_informations = LaundryInformationFactory.create_batch(size=3)
        tags = TagFactory.create_batch(size=3)
        cls.__product.laundry_informations.add(*laundry_informations)
        cls.__product.tags.add(*tags)

    def __get_expected_data(self, product):
        expected_data = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'sale_price': product.sale_price,
            'base_discount_rate': product.base_discount_rate,
            'base_discounted_price': product.base_discounted_price,
            'lining': product.lining,
            'materials': ProductMaterialSerializer(product.materials.all(), many=True).data,
            'colors': ProductColorSerializer(product.colors.all(), many=True).data,
            'images': ProductImageSerializer(product.images.all(), many=True).data,
            'manufacturing_country': product.manufacturing_country,
            'main_category': MainCategorySerializer(
                product.sub_category.main_category, exclude_fields=('sub_categories',)
                ).data,
            'sub_category': SubCategorySerializer(product.sub_category).data,
            'style': StyleSerializer(product.style).data,
            'age': AgeSerializer(product.age).data,
            'tags': TagSerializer(product.tags.all(), many=True).data,
            'laundry_informations': LaundryInformationSerializer(product.laundry_informations.all(), many=True).data,
            'thickness': ThicknessSerializer(product.thickness).data,
            'see_through': SeeThroughSerializer(product.see_through).data,
            'flexibility': FlexibilitySerializer(product.flexibility).data,
            'theme': ThemeSerializer(product.theme).data,
            'created_at': datetime_to_iso(product.created_at),
            'on_sale': product.on_sale,
            'code': product.code,
            'total_like': product.like_shoppers.all().count(),
        }

        return expected_data

    def test_model_instance_serialization_detail(self):
        expected_data = self.__get_expected_data(self.__product)
        expected_data['shopper_like'] = False
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(
                    prefetch_images
                ).annotate(total_like=Count('like_shoppers')).get(id=self.__product.id)

        self._test_model_instance_serialization(product, expected_data, context={'detail': True})

    def test_model_instance_serialization_list(self):
        expected_data = [
            self.__get_expected_data(self.__product)
        ]
        for data in expected_data:
            data['main_image'] = data['images'][0]['image_url']
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(
                    prefetch_images
                ).filter(id__in=[self.__product.id]).annotate(total_like=Count('like_shoppers'))
        serializer = self._get_serializer(product, many=True, context={'detail': False})
        
        for data in serializer.data:
            data.pop('shopper_like')

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

        self.assertDictEqual(
            {'id': serializer.data['id'], 'images': serializer.data['images']},
            expected_data
        )

    def test_default_image_list(self):
        ProductFactory()
        prefetch_images = Prefetch('images', to_attr='related_images')
        products = Product.objects.prefetch_related(prefetch_images).all()
        serializer = self._get_serializer(
            products, allow_fields=('id',), many=True, context={'detail': False}
        )
        expected_data = [
            {
                'id': product.id,
                'main_image': DEFAULT_IMAGE_URL if not product.images.all().exists() else BASE_IMAGE_URL + product.images.all()[0].image_url,
            }
            for product in products
        ]

        self.assertListEqual(
            [{'id': data['id'], 'main_image': data['main_image']} for data in serializer.data],
            expected_data
        )

    def test_model_instance_serialization_like_true(self):
        shopper = ShopperFactory()
        shopper.like_products.add(self.__product)

        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.__product.id)
        serializer = self._get_serializer(
            product, context={'detail': True, 'shopper_like': ProductLike.objects.filter(shopper=shopper, product=product).exists()}
        )
        
        self.assertEqual(serializer.data['shopper_like'], True)

    def test_model_instance_serialization_list_like_true(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        products = Product.objects.prefetch_related(
                    prefetch_images
                ).filter(id__in=[self.__product.id])
        shopper = ShopperFactory()
        shopper.like_products.add(*products)

        shoppers_like_products_id_list = list(shopper.like_products.all().values_list('id', flat=True))
        serializer = self._get_serializer(
            products, many=True, context={'detail': False, 'shoppers_like_products_id_list': shoppers_like_products_id_list})
        expected_data = [shopper.like_products.filter(id=product.id).exists() for product in products]

        self.assertListEqual(
            [data['shopper_like'] for data in serializer.data],
            expected_data
        )

    def test_model_instance_serialization_list_like_false(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        products = Product.objects.prefetch_related(
                    prefetch_images
                ).filter(id__in=[self.__product.id])
        serializer = self._get_serializer(products, many=True, context={'detail': False})
        expected_data = [False for _ in products]
        
        self.assertListEqual(
            [data['shopper_like'] for data in serializer.data],
            expected_data
        )


class ProductWriteSerializerTestCase(SerializerTestCase):
    __batch_size = 2
    fixtures = ['temporary_image']
    _serializer_class = ProductWriteSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__image_url_list = list(TemporaryImage.objects.all().values_list('image_url', flat=True))
        cls.__product = ProductFactory()
        ProductMaterialFactory.create_batch(size=cls.__batch_size, product=cls.__product, mixing_rate=50)

        cls.__product_colors = [
            ProductColorFactory(product=cls.__product, image_url=cls.__image_url_list.pop())
            for _ in range(cls.__batch_size)
        ]

        for product_color in cls.__product_colors:
            OptionFactory.create_batch(size=cls.__batch_size, product_color=product_color)

        for i in range(cls.__batch_size):
            ProductImageFactory(product=cls.__product, image_url=cls.__image_url_list.pop(), sequence=i+1)

        laundry_informations = LaundryInformationFactory.create_batch(size=cls.__batch_size)
        tags = TagFactory.create_batch(size=cls.__batch_size)
        cls.__product.laundry_informations.add(*laundry_informations)
        cls.__product.tags.add(*tags)

    def __get_input_data(self):
        tag_id_list = [tag.id for tag in TagFactory.create_batch(size=self.__batch_size)]
        laundry_information_id_list = [
            laundry_information.id for laundry_information in LaundryInformationFactory.create_batch(size=3)
        ]
        color_id_list = [color.id for color in ColorFactory.create_batch(size=2)]

        data = {
            'name': 'name',
            'price': 50000,
            'base_discount_rate': 10,
            'sub_category': self.__product.sub_category_id,
            'style': self.__product.style_id,
            'age': self.__product.age_id,
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
            'thickness': self.__product.thickness_id,
            'see_through': self.__product.see_through_id,
            'flexibility': self.__product.flexibility_id,
            'lining': True,
            'manufacturing_country': self.__product.manufacturing_country,
            'theme': self.__product.theme_id,
            'images': [
                {
                    'image_url': BASE_IMAGE_URL + self.__image_url_list.pop(),
                    'sequence': 1
                },
                {
                    'image_url': BASE_IMAGE_URL + self.__image_url_list.pop(),
                    'sequence': 2
                },
                {
                    'image_url': BASE_IMAGE_URL + self.__image_url_list.pop(),
                    'sequence': 3
                }
            ],
            'colors': [
                {
                    'color': color_id_list[0],
                    'display_color_name': '다크',
                    'options': [
                        {'size': 'Free'},
                        {'size': 'S'}
                    ],
                    'image_url': BASE_IMAGE_URL + self.__image_url_list.pop(),
                },
                {
                    'color': color_id_list[1],
                    'display_color_name': '블랙',
                    'options': [
                        {'size': 'Free'},
                        {'size': 'S'}
                    ],
                    'image_url': BASE_IMAGE_URL + self.__image_url_list.pop(),
                }
            ]
        }

        return data

    def test_validation_price(self):
        data = self.__get_input_data()
        data['price'] = 50010
        expected_message = 'The price must be a multiple of 100.'

        self._test_serializer_raise_validation_error(expected_message, data=data)

    def test_raise_validation_error_color_length_more_than_limit(self):
        product_colors = [
            ProductColorFactory(product=self.__product, image_url=self.__image_url_list.pop())
            for _ in range(PRODUCT_COLOR_MAX_LENGTH + 1)
        ]
        for product_color in product_colors:
            OptionFactory(product_color=product_color)
        data = [
            {
                'display_color_name': product_color.display_color_name,
                'color': product_color.color.id,
                'options': [
                    {'size': option.size}
                    for option in product_color.options.all()
                ],
                'image_url': BASE_IMAGE_URL + product_color.image_url,
            }for product_color in product_colors
        ]
        data += [
            {
                'id': product_color.id
            }for product_color in self.__product_colors
        ]
        expected_message = 'The product cannot have more than ten colors.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product, data={'colors': data}, partial=True
        )

    def test_raise_validation_error_delete_all_colors(self):
        data = [{'id': product_color.id} for product_color in self.__product.colors.all()]
        expected_message = 'The product must have at least one color.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product, data={'colors': data}, partial=True
        )

    def test_raise_validation_error_pass_non_unique_display_color_name(self):
        data = [
            {
                'id': self.__product_colors[0].id,
                'display_color_name': self.__product_colors[1].display_color_name
            }
        ]
        expected_message = 'The product with the display_color_name already exists.'
        
        self._test_serializer_raise_validation_error(
            expected_message, instance=self.__product, data={'colors': data}, partial=True
        )

    def test_make_price_data(self):
        price = 50000
        base_discount_rate = 20
        data = self.__get_input_data()
        data['price'] = price
        data['base_discount_rate'] = base_discount_rate
        
        serializer = self._get_serializer_after_validation(data=data, context={'wholesaler': WholesalerFactory()})
        product = serializer.save()

        expected_sale_price = 50000 * 2
        expected_base_discounted_price = expected_sale_price - (expected_sale_price * base_discount_rate/100) // 100 * 100

        self.assertEqual(expected_sale_price, product.sale_price)
        self.assertEqual(expected_base_discounted_price, product.base_discounted_price)

    def test_create(self):
        data = self.__get_input_data()
        serializer = self._get_serializer_after_validation(
            data=data, context={'wholesaler': WholesalerFactory()}
        )
        product = serializer.save()

        self.assertTrue(Product.objects.filter(id=product.id).exists())
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
                product.laundry_informations.all().order_by('id').values_list('id', flat=True)
            ),
            data['laundry_informations']
        )
        self.assertEqual(product.images.all().count(), len(data['images']))
        self.assertEqual(product.materials.all().count(), len(data['materials']))
        self.assertEqual(product.colors.all().count(), len(data['colors']))
        self.assertEqual(
            Option.objects.filter(product_color__product=product).count(),
            sum([len(color_data['options']) for color_data in data['colors']])
        )

    def test_update_product_attribute(self):
        update_data = {}
        update_data['name'] = self.__product.name + '_update'
        update_data['price'] = self.__product.price + 10000
        update_data['sub_category'] = SubCategoryFactory().id
        update_data['style'] = StyleFactory().id
        update_data['age'] = AgeFactory().id
        update_data['thickness'] = ThicknessFactory().id
        update_data['see_through'] = SeeThroughFactory().id
        update_data['flexibility'] = FlexibilityFactory().id
        update_data['lining'] = not self.__product.lining
        update_data['manufacturing_country'] = self.__product.manufacturing_country + '_update'
        update_data['theme'] = ThemeFactory().id
        serializer = self._get_serializer_after_validation(
            self.__product, data=update_data, partial=True
        )
        product = serializer.save()

        self.assertTrue(Product.objects.filter(id=product.id).exists())
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
            list(self.__product.tags.all().values_list('id', flat=True)), 
            2
        )
        tag_id_list = [tag.id for tag in tags] + remaining_tags
        tag_id_list.sort()

        update_data = {'tags': tag_id_list}
        serializer = self._get_serializer_after_validation(
            self.__product, data=update_data, partial=True
        )
        product = serializer.save()

        self.assertListEqual(
            list(product.tags.all().order_by('id').values_list('id', flat=True)),
            tag_id_list
        )

    def test_update_many_to_one_fields(self):
        materials = self.__product.materials.all()
        delete_materials = materials[:1]
        update_materials = materials[1:]
        create_data = [
            {
                'material': 'matcreate',
            }
        ]
        delete_data = list(delete_materials.values('id'))
        update_data = [
            {
                'id': material.id,
                'material': material.material + 'update',
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
            self.__product, data=data, partial=True
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
        delete_product_color_id = self.__product.colors.latest('id').id
        data = {
            'colors': [
                {'id': delete_product_color_id}
            ]
        }
        serializer = self._get_serializer_after_validation(
            self.__product, data=data, partial=True
        )
        serializer.save()
        self.assertTrue(not ProductColor.objects.get(id=delete_product_color_id).on_sale)
        self.assertTrue(
            not Option.objects.filter(product_color_id=delete_product_color_id, on_sale=True).exists()
        )

    def test_create_product_colors_in_update(self):
        existing_color_id_list = list(self.__product.colors.all().values_list('id', flat=True))
        create_color_data = self.__get_input_data()['colors']
        create_option_data = [
            option_data for color_data in create_color_data for option_data in color_data['options']
        ]
        data = {'colors': create_color_data}
        serializer = self._get_serializer_after_validation(
            self.__product, data=data, partial=True
        )
        serializer.save()

        self.assertListEqual(
            list(
                ProductColor.objects.filter(product=self.__product).exclude(id__in=existing_color_id_list)
                .order_by('id').values('color', 'display_color_name', 'image_url')
            ),
            [
                {
                    'color': d['color'],
                    'display_color_name': d['display_color_name']
                        if d['display_color_name'] is not None
                        else Color.objects.get(id=d['color']).name,
                    'image_url': d['image_url'].split(BASE_IMAGE_URL)[-1],
                }for d in data['colors']
            ]
        )
        self.assertListEqual(
            list(
                Option.objects.filter(product_color__product=self.__product)
                .exclude(product_color_id__in=existing_color_id_list).order_by('id')
                .values('size')
            ),
            [
                {'size': data['size']}
                for data in create_option_data
            ]
        )

    def test_update_product_colors_except_options(self):
        update_color_obj = self.__product.colors.latest('id')
        update_image_url = TemporaryImage.objects.first().image_url
        update_data = {
            'id': update_color_obj.id,
            'display_color_name': '_updated',
            'image_url': BASE_IMAGE_URL + update_image_url
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.__product, data=data, partial=True
        )
        serializer.save()

        updated_color_obj = self.__product.colors.get(id=update_color_obj.id)
        expected_dict = update_data
        expected_dict['image_url'] = update_image_url

        self.assertDictEqual(
            model_to_dict(updated_color_obj, fields=('id', 'display_color_name', 'image_url')),
            expected_dict
        )

    def test_create_option_in_update(self):
        update_color_obj = self.__product.colors.latest('id')
        existing_option_id_list = list(update_color_obj.options.values_list('id', flat=True))
        update_data = {
            'id': update_color_obj.id,
            'options': [
                {'size': 'Free'}
            ]
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.__product, data=data, partial=True
        )
        serializer.save()

        self.assertListEqual(
            list(
                Option.objects.filter(product_color=update_color_obj).exclude(id__in=existing_option_id_list)
                .order_by('id').values('size')
            ),
            update_data['options']
        )

    def test_update_price(self):
        update_data = {'price': 60000}
        serializer = self._get_serializer_after_validation(
            self.__product, data=update_data, partial=True
        )
        product = serializer.save()
        expected_sale_price = update_data['price'] * 2
        expected_base_discounted_price = expected_sale_price - (expected_sale_price * product.base_discount_rate / 100) // 100 * 100

        self.assertEqual(product.price, update_data['price'])
        self.assertEqual(product.sale_price, expected_sale_price)
        self.assertEqual(product.base_discounted_price, expected_base_discounted_price)

    def test_update_base_discount_rate(self):
        update_data = {'base_discount_rate': 20}
        serializer = self._get_serializer_after_validation(
            self.__product, data=update_data, partial=True
        )
        product = serializer.save()
        expected_base_discounted_price = product.sale_price - (product.sale_price * product.base_discount_rate / 100) // 100 * 100

        self.assertEqual(product.base_discounted_price, expected_base_discounted_price)

    def test_update_price_and_base_discount_rate(self):
        update_data = {'price': 60000, 'base_discount_rate': 20}
        serializer = self._get_serializer_after_validation(
            self.__product, data=update_data, partial=True
        )
        product = serializer.save()
        expected_sale_price = update_data['price'] * 2
        expected_base_discounted_price = expected_sale_price - (expected_sale_price * product.base_discount_rate / 100) // 100 * 100

        self.assertEqual(product.price, update_data['price'])
        self.assertEqual(product.sale_price, expected_sale_price)
        self.assertEqual(product.base_discounted_price, expected_base_discounted_price)
        

    def test_delete_option(self):
        update_color_obj = self.__product.colors.latest('id')
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
            self.__product, data=data, partial=True
        )
        serializer.save()

        self.assertTrue(not Option.objects.get(id=delete_option_id).on_sale)


class ProductQuestionAnswerClassificationSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductQuestionAnswerClassificationSerializer

    def test_model_instance_serialization(self):
        classification = ProductQuestionAnswerClassificationFactory()
        expected_data = {
            'id': classification.id,
            'name': classification.name,
        }

        self._test_model_instance_serialization(classification, expected_data)


class ProductQuestionAnswerSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductQuestionAnswerSerializer

    @classmethod
    def setUpTestData(cls):
        cls.__question_answer = ProductQuestionAnswerFactory()

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.__question_answer.id,
            'shopper': self.__question_answer.shopper.id,
            'created_at': datetime_to_iso(self.__question_answer.created_at),
            'username': self.__question_answer.shopper.username[:3] + '***',
            'classification': self.__question_answer.classification.name,
            'question': self.__question_answer.question,
            'answer': self.__question_answer.answer,
            'is_secret': self.__question_answer.is_secret,
        }

        self._test_model_instance_serialization(self.__question_answer, expected_data)

    def test_create(self):
        product = ProductFactory()
        shopper = ShopperFactory()
        data = {
            'question': 'question',
            'is_secret': True,
            'classification': ProductQuestionAnswerClassificationFactory().id,
        }
        serializer = self._get_serializer_after_validation(data=data)
        question_answer = serializer.save(product=product, shopper=shopper)

        self.assertTrue(ProductQuestionAnswer.objects.filter(id=question_answer.id).exists())
        self.assertEqual(question_answer.product, product)
        self.assertEqual(question_answer.shopper, shopper)
        self.assertEqual(question_answer.classification.id, data['classification'])
        self.assertEqual(question_answer.question, data['question'])
        self.assertEqual(question_answer.is_secret, data['is_secret'])

    def test_update(self):
        data = {
            'question': self.__question_answer.question + '_update',
            'is_secret': not self.__question_answer.is_secret,
            'classification':ProductQuestionAnswerClassificationFactory().id
        }

        serializer = self._get_serializer_after_validation(self.__question_answer, data=data)
        question_answer = serializer.save()

        self.assertTrue(ProductQuestionAnswer.objects.filter(id=question_answer.id).exists())
        self.assertEqual(question_answer.question, data['question'])
        self.assertEqual(question_answer.is_secret, data['is_secret'])
        self.assertEqual(question_answer.classification.id, data['classification'])
