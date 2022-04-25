import random, copy

from django.test import tag
from django.db.models.query import Prefetch
from django.db.models import Count
from django.forms import model_to_dict

from common.models import TemporaryImage
from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL, datetime_to_iso
from common.test.test_cases import SerializerTestCase, ListSerializerTestCase
from user.test.factory import WholesalerFactory, ShopperFactory
from user.models import ProductLike
from .factory import (
    ProductColorFactory, ProductFactory, SubCategoryFactory, MainCategoryFactory, ColorFactory, SizeFactory, LaundryInformationFactory, 
    TagFactory, ThemeFactory, ThicknessFactory, SeeThroughFactory, FlexibilityFactory, AgeFactory, StyleFactory, MaterialFactory, ProductImageFactory,
    ProductMaterialFactory, OptionFactory, ThemeFactory, 
)
from ..serializers import (
    ProductMaterialSerializer, SubCategorySerializer, MainCategorySerializer, ColorSerializer, SizeSerializer, LaundryInformationSerializer, 
    ThicknessSerializer, SeeThroughSerializer, ProductColorSerializer, FlexibilitySerializer, AgeSerializer, StyleSerializer, MaterialSerializer, 
    ProductImageSerializer, OptionSerializer, ProductSerializer, ProductReadSerializer, ProductWriteSerializer, TagSerializer, ThemeSerializer,
    PRODUCT_IMAGE_MAX_LENGTH, PRODUCT_COLOR_MAX_LENGTH,
)
from ..models import Product, ProductColor, Color, Option, ProductMaterial


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
        cls.image_url = TemporaryImage.objects.first().image_url
        cls.product_image = ProductImageFactory()
        cls.data = {
            'image_url': BASE_IMAGE_URL + cls.image_url,
            'sequence': 1
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product_image.id,
            'image_url': BASE_IMAGE_URL + self.product_image.image_url,
            'sequence': self.product_image.sequence,
        }

        self._test_model_instance_serialization(self.product_image, expected_data)

    def test_deserialization(self):
        expected_validated_data = {
            'image_url': self.image_url,
            'sequence': self.data['sequence']
        }

        self._test_deserialzation(self.data, expected_validated_data)

    def test_raise_validation_error_create_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)

        expected_message = '{0} field is required.'.format(key)
        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_image, data=self.data, partial=True
        )

    def test_raise_validation_error_update_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        self.data['id'] = self.product_image.id

        expected_message = '{0} field is required.'.format(key)
        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_image, data=self.data, partial=True
        )


class ProductImageListSerializerTestCase(ListSerializerTestCase):
    fixtures = ['temporary_image']
    _child_serializer_class = ProductImageSerializer
    batch_size = 3

    @classmethod
    def setUpTestData(cls):
        temporary_images = list(TemporaryImage.objects.all().values_list('image_url', flat=True))
        cls.product = ProductFactory()
        cls.product_images = [
            ProductImageFactory(product=cls.product, sequence=i+1)
            for i in range(cls.batch_size)
        ]
        cls.data = [
            {
                'image_url': BASE_IMAGE_URL + temporary_images[i],
                'sequence': i+1
            } for i in range(cls.batch_size)
        ]

    def test_raise_validation_error_data_length_more_than_upper_limit(self):
        data = [
            {
                'image_url': BASE_IMAGE_URL + 'product/sample/product_{0}.jpg'.format(i+1),
                'sequence': i+1,
            } for i in range(PRODUCT_IMAGE_MAX_LENGTH + 1)
        ]
        expected_message = 'The product cannot have more than ten images.'

        self._test_serializer_raise_validation_error(expected_message, data=data)

    def test_raise_validation_error_sequences_not_startswith_one(self):
        for d in self.data:
            d['sequence'] += 1
        expected_message = 'The sequence of the images must be ascending from 1 to n.'

        self._test_serializer_raise_validation_error(expected_message, data=self.data)

    def test_raise_validation_error_omitted_sequences(self):
        self.data[-1]['sequence'] += 1
        expected_message = 'The sequence of the images must be ascending from 1 to n.'

        self._test_serializer_raise_validation_error(expected_message, data=self.data)

    def test_raise_validation_error_data_length_is_zero(self):
        data = [
            {'id': product_image.id} 
            for product_image in self.product_images
        ]
        expected_message = 'The product must have at least one image.'

        self._test_serializer_raise_validation_error(expected_message, data=data, partial=True)


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

    def test_raise_validation_error_create_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_material, data=self.data, partial=True
        )
        
    def test_raise_validation_error_update_data_does_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        self.data['id'] = self.product_material.id
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_material, data=self.data, partial=True
        )


class ProductMaterialListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = ProductMaterialSerializer
    materials_num = 2

    @classmethod
    def setUpTestData(cls):
        total_mixing_rates = cls._child_serializer_class.Meta.list_serializer_class.total_mixing_rates
        mixing_rate = total_mixing_rates / cls.materials_num

        cls.product = ProductFactory()
        cls.product_materials = ProductMaterialFactory.create_batch(
            cls.materials_num, product=cls.product, mixing_rate=mixing_rate
        )
        cls.data = [
            {
                'material': ProductMaterialFactory.build().material,
                'mixing_rate': mixing_rate
            }for i in range(cls.materials_num)
        ]

    def test_raise_validation_error_total_mixing_rates_does_not_match_criteria(self):
        data = self.data
        data[0]['mixing_rate'] += 10
        expected_message = 'The total of material mixing rates must be 100.'

        self._test_serializer_raise_validation_error(
            expected_message, data=data
        )

    def test_raise_validation_error_duplicated_material_name(self):
        data = self.data
        data[-1]['material'] = data[0]['material']
        expected_message = 'Material is duplicated.'

        self._test_serializer_raise_validation_error(
            expected_message, data=data
        )


class OptionSerializerTestCase(SerializerTestCase):
    _serializer_class = OptionSerializer

    @classmethod
    def setUpTestData(cls):
        size = SizeFactory()
        cls.option = OptionFactory(size = size.name)
        cls.data = {'size': 'Free'}

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.option.id, 
            'size': self.option.size,
            'on_sale': self.option.on_sale,
        }

        self._test_model_instance_serialization(self.option, expected_data)

    def test_raise_validation_error_update_size_data(self):
        self.data['id'] = self.option.id
        self.data['size'] = self.data['size'] + 'update'
        expected_message = 'Size data cannot be updated.'

        self._test_serializer_raise_validation_error(
            expected_message, data=self.data, partial=True
        )


class OptionListSerializerTestCase(ListSerializerTestCase):
    _child_serializer_class = OptionSerializer
    options_num = 3

    @classmethod
    def setUpTestData(cls):
        cls.product_color = ProductColorFactory()
        cls.options = OptionFactory.create_batch(size=cls.options_num, product_color=cls.product_color)
        cls.create_data = [
            {'size': SizeFactory().id}
            for _ in range(cls.options_num)
        ]

    def test_raise_validation_error_duplicated_size_data_in_create(self):
        data = self.create_data
        data[-1]['size'] = data[0]['size']
        expected_message = 'Size is duplicated.'

        self._test_serializer_raise_validation_error(expected_message, data=data)

    def test_raise_validation_error_duplicated_size_data_in_update(self):
        self.create_data[-1]['size'] = self.create_data[0]['size']
        data = self.create_data
        expected_message = 'Size is duplicated.'

        self._test_serializer_raise_validation_error(
            expected_message, data=data, partial=True
        )
    

class ProductColorSerializerTestCase(SerializerTestCase):
    fixtures = ['temporary_image']
    _serializer_class = ProductColorSerializer
    options_num = 3

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
                {'size': option.size}
                for option in cls.options
            ],
            'image_url': BASE_IMAGE_URL + TemporaryImage.objects.first().image_url,
        }

    def test_model_instance_serialization(self):
        expected_data = {
            'id': self.product_color.id,
            'display_color_name': self.product_color.display_color_name,
            'color': self.product_color.color.id,
            'options': OptionSerializer(self.options, many=True).data,
            'image_url': BASE_IMAGE_URL + self.product_color.image_url,
            'on_sale': self.product_color.on_sale,
        }
        self._test_model_instance_serialization(self.product_color, expected_data)

    def test_raise_validation_error_update_color_data(self):
        color = ColorFactory()
        self.data['id'] = self.product_color.id
        self.data['color'] = color.id
        expected_message = 'Color data cannot be updated.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_color, data=self.data, partial=True
        )

    def test_raise_validation_error_create_data_not_include_all_required_field_in_partial(self):
        key = random.choice(list(self.data.keys()))
        self.data.pop(key)
        expected_message = '{0} field is required.'.format(key)

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_color, data=self.data, partial=True
        )

    def test_raise_validation_error_update_non_unique_size_in_partial(self):
        self.data['id'] = self.product_color.id
        new_option_data = {'size': self.options[1].size}
        self.data['options'] = [new_option_data]
        expected_message = 'The option with the size already exists.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_color, data=self.data, partial=True
        )

    def test_raise_validation_error_delete_all_options(self):
        data = {
            'id': self.product_color.id,
            'options': [
                {'id': option.id}
                for option in self.options
            ]
        }
        expected_message = 'The product color must have at least one option.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product_color, data=data, partial=True
        )


class ProductColorListSerializerTestCase(ListSerializerTestCase):
    fixtures = ['temporary_image']
    _child_serializer_class = ProductColorSerializer
    batch_size = 3

    @classmethod
    def setUpTestData(cls):
        cls.temporary_images = list(TemporaryImage.objects.all().values_list('image_url', flat=True))
        cls.product = ProductFactory()

        for i in range(cls.batch_size):
            ProductColorFactory(product=cls.product, image_url=cls.temporary_images[i])
        for product_color in cls.product.colors.all():
            OptionFactory(product_color=product_color)

        cls.update_data = [
            {
                'id': product_color.id,
                'display_color_name': product_color.display_color_name,
                'color': product_color.color.id,
                'options': [
                    {
                        'id': option.id,
                        'size': option.size,
                    }for option in product_color.options.all()
                ],
                'image_url': BASE_IMAGE_URL + product_color.image_url,
            }for product_color in cls.product.colors.all()
        ]

        cls.create_data = copy.deepcopy(cls.update_data)
        for data in cls.create_data:
            data.pop('id')

    def test_raise_validation_error_input_data_length_more_than_upper_limit(self):
        for i in range(PRODUCT_COLOR_MAX_LENGTH - self.batch_size + 1):
            ProductColorFactory(product=self.product, image_url=self.temporary_images[i+self.batch_size])

        product_colors = self.product.colors.all()
        for product_color in product_colors:
            OptionFactory(product_color=product_color)

        data = [
            {
                'display_color_name': product_color.display_color_name,
                'color': product_color.color.id,
                'options': [
                    {
                        'id': option.id,
                        'size': option.size,
                    }for option in product_color.options.all()
                ],
                'image_url': BASE_IMAGE_URL + product_color.image_url,
            }for product_color in product_colors
        ]
        expected_message = 'The product cannot have more than ten colors.'

        self._test_serializer_raise_validation_error(
            expected_message, data=data
        )

    def test_raise_validation_error_display_color_name_duplicated_in_create(self):
        self.create_data[-1]['display_color_name'] = self.create_data[0]['display_color_name']
        expected_message = 'display_color_name is duplicated.'

        self._test_serializer_raise_validation_error(
            expected_message, data=self.create_data
        )

    def test_raise_validation_error_display_color_name_duplicated_in_update(self):
        self.update_data[-1]['display_color_name'] = self.update_data[0]['display_color_name']
        expected_message = 'display_color_name is duplicated.'

        self._test_serializer_raise_validation_error(
            expected_message, data=self.update_data, partial=True
        )


class ProductSerializerTestCase(SerializerTestCase):
    _serializer_class = ProductSerializer

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()

    def test_sort_dictionary_by_field_name(self):
        fields = list(self._get_serializer().get_fields().keys())
        random.shuffle(fields)

        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.product.id)
        serializer = self._get_serializer(product, context={'field_order': fields})

        self.assertListEqual(list(serializer.data.keys()), fields)


class ProductReadSerializerTestCase(SerializerTestCase):
    maxDiff = None
    _serializer_class = ProductReadSerializer
    fixtures = ['membership']

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        ProductMaterialFactory(product=cls.product)
        ProductColorFactory(product=cls.product)
        ProductImageFactory.create_batch(size=3, product=cls.product)
        laundry_informations = LaundryInformationFactory.create_batch(size=3)
        tags = TagFactory.create_batch(size=3)
        cls.product.laundry_informations.add(*laundry_informations)
        cls.product.tags.add(*tags)

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
            'created': datetime_to_iso(product.created),
            'on_sale': product.on_sale,
            'code': product.code,
            'total_like': product.like_shoppers.all().count(),
        }

        return expected_data

    def test_model_instance_serialization_detail(self):
        expected_data = self.__get_expected_data(self.product)
        expected_data['shopper_like'] = False
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(
                    prefetch_images
                ).annotate(total_like=Count('like_shoppers')).get(id=self.product.id)

        self._test_model_instance_serialization(product, expected_data, context={'detail': True})

    def test_model_instance_serialization_list(self):
        expected_data = [
            self.__get_expected_data(self.product)
        ]
        for data in expected_data:
            data['main_image'] = data['images'][0]['image_url']
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(
                    prefetch_images
                ).filter(id__in=[self.product.id]).annotate(total_like=Count('like_shoppers'))
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
        shopper.like_products.add(self.product)

        prefetch_images = Prefetch('images', to_attr='related_images')
        product = Product.objects.prefetch_related(prefetch_images).get(id=self.product.id)
        serializer = self._get_serializer(
            product, context={'detail': True, 'shopper_like': ProductLike.objects.filter(shopper=shopper, product=product).exists()}
        )
        
        self.assertEqual(serializer.data['shopper_like'], True)

    def test_model_instance_serialization_list_like_true(self):
        prefetch_images = Prefetch('images', to_attr='related_images')
        products = Product.objects.prefetch_related(
                    prefetch_images
                ).filter(id__in=[self.product.id])
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
                ).filter(id__in=[self.product.id])
        serializer = self._get_serializer(products, many=True, context={'detail': False})
        expected_data = [False for _ in products]
        
        self.assertListEqual(
            [data['shopper_like'] for data in serializer.data],
            expected_data
        )

class ProductWriteSerializerTestCase(SerializerTestCase):
    batch_size = 2
    fixtures = ['temporary_image']
    _serializer_class = ProductWriteSerializer

    @classmethod
    def setUpTestData(cls):
        cls.image_url_list = list(TemporaryImage.objects.all().values_list('image_url', flat=True))
        cls.product = ProductFactory()
        ProductMaterialFactory.create_batch(size=cls.batch_size, product=cls.product, mixing_rate=50)

        cls.product_colors = [
            ProductColorFactory(product=cls.product, image_url=cls.image_url_list.pop())
            for _ in range(cls.batch_size)
        ]

        for product_color in cls.product_colors:
            OptionFactory.create_batch(size=cls.batch_size, product_color=product_color)

        for i in range(cls.batch_size):
            ProductImageFactory(product=cls.product, image_url=cls.image_url_list.pop(), sequence=i+1)

        laundry_informations = LaundryInformationFactory.create_batch(size=cls.batch_size)
        tags = TagFactory.create_batch(size=cls.batch_size)
        cls.product.laundry_informations.add(*laundry_informations)
        cls.product.tags.add(*tags)

    def __get_input_data(self):
        product = ProductFactory()
        tag_id_list = [tag.id for tag in TagFactory.create_batch(size=self.batch_size)]
        tag_id_list.sort()
        laundry_information_id_list = [
            laundry_information.id for laundry_information in LaundryInformationFactory.create_batch(size=3)
        ]
        laundry_information_id_list.sort()
        color_id_list = [color.id for color in ColorFactory.create_batch(size=2)]

        data = {
            'name': 'name',
            'price': 50000,
            'base_discount_rate': 10,
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
                    'image_url': BASE_IMAGE_URL + self.image_url_list.pop(),
                    'sequence': 1
                },
                {
                    'image_url': BASE_IMAGE_URL + self.image_url_list.pop(),
                    'sequence': 2
                },
                {
                    'image_url': BASE_IMAGE_URL + self.image_url_list.pop(),
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
                    'image_url': BASE_IMAGE_URL + self.image_url_list.pop(),
                },
                {
                    'color': color_id_list[1],
                    'display_color_name': '블랙',
                    'options': [
                        {'size': 'Free'},
                        {'size': 'S'}
                    ],
                    'image_url': BASE_IMAGE_URL + self.image_url_list.pop(),
                }
            ]
        }

        return data

    def test_validaation_price(self):
        data = self.__get_input_data()
        data['price'] = 50010
        expected_message = 'The price must be a multiple of 100.'

        self._test_serializer_raise_validation_error(expected_message, data=data)

    def test_raise_validation_error_does_not_pass_all_exact_image_data_in_partial(self):
        data = [
            {
                'id': image.id,
                'image_url': BASE_IMAGE_URL + image.image_url,
                'sequence': image.sequence,
            } for image in list(self.product.images.all())[:-1]
        ]
        expected_message = 'You must contain all exact data that the product has.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product, data={'images': data}, partial=True
        )

    def test_raise_validation_erorr_does_not_pass_all_exact_material_data(self):
        data = [
            {
                'id': material.id,
                'material': material.material,
                'mixing_rate': material.mixing_rate,
            } for material in list(self.product.materials.all())[:-1]
        ]
        data[0]['mixing_rate'] += data[-1]['mixing_rate']
        expected_message = 'You must contain all exact data that the product has.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product, data={'materials': data}, partial=True
        )

    def test_raise_validation_error_color_length_more_than_limit(self):
        product_colors = [
            ProductColorFactory(product=self.product, image_url=self.image_url_list.pop())
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
            }for product_color in self.product_colors
        ]
        expected_message = 'The product cannot have more than ten colors.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product, data={'colors': data}, partial=True
        )

    def test_raise_validation_error_delete_all_colors(self):
        data = [{'id': product_color.id} for product_color in self.product.colors.all()]
        expected_message = 'The product must have at least one color.'

        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product, data={'colors': data}, partial=True
        )

    def test_raise_validation_error_pass_non_unique_display_color_name(self):
        data = [
            {
                'id': self.product_colors[0].id,
                'display_color_name': self.product_colors[1].display_color_name
            }
        ]
        expected_message = 'The product with the display_color_name already exists.'
        
        self._test_serializer_raise_validation_error(
            expected_message, instance=self.product, data={'colors': data}, partial=True
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
                    'image_url': data['image_url'].split(BASE_IMAGE_URL)[-1],
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
                    'image_url': data['image_url'].split(BASE_IMAGE_URL)[-1],
                }for data in data['colors']
            ]
        )
        self.assertListEqual(
            list(Option.objects.filter(product_color__product=product).order_by('id')
            .values('size')),
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
        self.assertTrue(not ProductColor.objects.get(id=delete_product_color_id).on_sale)
        self.assertTrue(
            not Option.objects.filter(product_color_id=delete_product_color_id, on_sale=True).exists()
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
                    'image_url': d['image_url'].split(BASE_IMAGE_URL)[-1],
                }for d in data['colors']
            ]
        )
        self.assertListEqual(
            list(
                Option.objects.filter(product_color__product=self.product)
                .exclude(product_color_id__in=existing_color_id_list).order_by('id')
                .values('size')
            ),
            [
                {'size': data['size']}
                for data in create_option_data
            ]
        )

    def test_update_product_colors_except_options(self):
        update_color_obj = self.product.colors.latest('id')
        update_image_url = TemporaryImage.objects.first().image_url
        update_data = {
            'id': update_color_obj.id,
            'display_color_name': '_updated',
            'image_url': BASE_IMAGE_URL + update_image_url
        }
        data = {'colors': [update_data]}
        serializer = self._get_serializer_after_validation(
            self.product, data=data, partial=True
        )
        serializer.save()

        updated_color_obj = self.product.colors.get(id=update_color_obj.id)
        expected_dict = update_data
        expected_dict['image_url'] = update_image_url

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
                {'size': 'Free'}
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
                .order_by('id').values('size')
            ),
            update_data['options']
        )

    def test_update_price(self):
        update_data = {'price': 60000}
        serializer = self._get_serializer_after_validation(
            self.product, data=update_data, partial=True
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
            self.product, data=update_data, partial=True
        )
        product = serializer.save()
        expected_base_discounted_price = product.sale_price - (product.sale_price * product.base_discount_rate / 100) // 100 * 100

        self.assertEqual(product.base_discounted_price, expected_base_discounted_price)

    def test_update_price_and_base_discount_rate(self):
        update_data = {'price': 60000, 'base_discount_rate': 20}
        serializer = self._get_serializer_after_validation(
            self.product, data=update_data, partial=True
        )
        product = serializer.save()
        expected_sale_price = update_data['price'] * 2
        expected_base_discounted_price = expected_sale_price - (expected_sale_price * product.base_discount_rate / 100) // 100 * 100

        self.assertEqual(product.price, update_data['price'])
        self.assertEqual(product.sale_price, expected_sale_price)
        self.assertEqual(product.base_discounted_price, expected_base_discounted_price)
        

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
