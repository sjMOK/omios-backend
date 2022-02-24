from django.test import tag

from freezegun import freeze_time
from datetime import datetime
from pdb import set_trace

from common.test.test_cases import ModelTestCase, FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from user.test.factory import WholesalerFactory
from ..models import (
    MainCategory, SubCategory, Product, Age, Thickness, SeeThrough, Flexibility, ProductAdditionalInformation, ProductImages,
    Tag, Color, ProductColor, ProductColorImages, Size, Option, Keyword, Style, LaundryInformation, Material, ProductMaterial, 
)
from .factory import (
    AgeFactory, LaundryInformationFactory, MainCategoryFactory, StyleFactory, SubCategoryFactory, ProductFactory, TagFactory, ThicknessFactory,
    SeeThroughFactory, FlexibilityFactory, ColorFactory, ProductColorFactory, SizeFactory,
)


class MainCategoryTest(ModelTestCase):
    _model_class = MainCategory
    
    def setUp(self):
        self._test_data = {
            'name': '아우터',
            'image_url': 'category/outer.svg',
        }

    def test_create(self):
        main_category = self._get_model_after_creation()
        
        self.assertEqual(main_category.name, self._test_data['name'])
        self.assertEqual(main_category.image_url.name, self._test_data['image_url'])


class SubCategoryTest(ModelTestCase):
    _model_class = SubCategory

    @classmethod
    def setUpTestData(cls):
        cls._main_category = MainCategoryFactory()

    def setUp(self):
        self._test_data = {
            'main_category': self._main_category,
            'name': '가디건',
            'require_product_additional_information': True,
            'require_laundry_information': True,
        }

    def test_create(self):
        sub_category = self._get_model_after_creation()
        
        self.assertEqual(sub_category.name, self._test_data['name'])
        self.assertEqual(sub_category.main_category, self._test_data['main_category'])
        self.assertTrue(sub_category.require_product_additional_information)
        self.assertTrue(sub_category.require_laundry_information)

@tag('product')
class ProductTest(ModelTestCase):
    _model_class = Product

    @classmethod
    def setUpTestData(cls):
        wholesaler = WholesalerFactory(username='musinsa')
        sub_category = SubCategoryFactory()
        age = AgeFactory()
        style = StyleFactory()

        cls._test_data = {
            'wholesaler': wholesaler,
            'sub_category': sub_category,
            'name': '크로커다일레이디 크로커다일 베이직플리스점퍼 cl0wpf903',
            'price': 35000,
            'age': age,
            'style': style,
        }   

        cls._product = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertEqual(self._product.wholesaler, self._test_data['wholesaler'])
        self.assertEqual(self._product.name, self._test_data['name'])
        self.assertEqual(self._product.sub_category, self._test_data['sub_category'])
        self.assertEqual(self._product.price, self._test_data['price'])
        self.assertEqual(self._product.age, self._test_data['age'])
        self.assertEqual(self._product.style, self._test_data['style'])
    
    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create_default_values(self):
        product = self._get_model_after_creation()

        self.assertEqual(product.code, 'AA')
        self.assertEqual(product.created, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertTrue(product.on_sale)

    def test_add_laundry_informations(self):
        laundry_information_id_list = [laundry.id for laundry in LaundryInformationFactory.create_batch(3)]
        laundry_informations = LaundryInformation.objects.filter(id__in=laundry_information_id_list)
        self._product.laundry_informations.add(*laundry_informations)

        self.assertQuerysetEqual(self._product.laundry_informations.all(), laundry_informations, ordered=False)

    def test_add_tags(self):
        tag_id_list = [tag.id for tag in TagFactory.create_batch(3)]
        tags = Tag.objects.filter(id__in=tag_id_list)
        self._product.tags.add(*tags)

        self.assertQuerysetEqual(self._product.tags.all(), tags, ordered=False)


class AgeTest(ModelTestCase):
    _model_class = Age

    def setUp(self):
        self._test_data = {
            'name': '20대 중반',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class ThicknessTest(ModelTestCase):
    _model_class = Thickness

    def setUp(self):
        self._test_data = {
            'name': '두꺼움',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class SeeThroughTest(ModelTestCase):
    _model_class = SeeThrough

    def setUp(self):
        self._test_data = {
            'name': '비침',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class FlexibilityTest(ModelTestCase):
    _model_class = Flexibility

    def setUp(self):
        self._test_data = {
            'name': '높음',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])        


class ProductAdditionalInformationTest(ModelTestCase):
    _model_class = ProductAdditionalInformation

    def setUp(self):
        product = ProductFactory()
        thickness = ThicknessFactory()
        see_through = SeeThroughFactory()
        flexibility = FlexibilityFactory()

        self._test_data = {
            'product': product,
            'thickness': thickness,
            'see_through': see_through,
            'flexibility': flexibility,
            'lining': True,
        }

    def test_create(self):
        product_additional_inforamtion = self._get_model_after_creation()

        self.assertEqual(product_additional_inforamtion.product, self._test_data['product'])
        self.assertEqual(product_additional_inforamtion.thickness, self._test_data['thickness'])
        self.assertEqual(product_additional_inforamtion.see_through, self._test_data['see_through'])
        self.assertEqual(product_additional_inforamtion.flexibility, self._test_data['flexibility'])
        self.assertTrue(product_additional_inforamtion.lining)


class ProductImagesTest(ModelTestCase):
    _model_class = ProductImages

    def setUp(self):
        product = ProductFactory()

        self._test_data = {
            'product': product,
            'image_url': 'product/sample/product_5.jpg',
            'sequence': 1,
        }

    def test_create(self):
        product_image = self._get_model_after_creation()

        self.assertEqual(product_image.product, self._test_data['product'])
        self.assertEqual(product_image.image_url, self._test_data['image_url'])
        self.assertEqual(product_image.sequence, self._test_data['sequence'])


class TagTest(ModelTestCase):
    _model_class = Tag

    def setUp(self):
        self._test_data = {
            'name': '남친룩',
        }

    def test_create(self):
        tag = self._get_model_after_creation()

        self.assertEqual(tag.name, self._test_data['name'])
        

class ColorTest(ModelTestCase):
    _model_class = Color

    def setUp(self):
        self._test_data = {
            'name': '블랙',
            'image_url': 'color/black.svg',
        }

    def test_create(self):
        color = self._get_model_after_creation()

        self.assertEqual(color.name, self._test_data['name'])
        self.assertEqual(color.image_url.name, self._test_data['image_url'])


class ProductColorTest(ModelTestCase):
    _model_class = ProductColor

    @classmethod
    def setUpTestData(cls):
        product = ProductFactory()
        color = ColorFactory()

        cls._test_data = {
            'product': product,
            'color': color,
            'display_color_name': 'display_color_name',
        }

        cls._product_color = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertEqual(self._product_color.product, self._test_data['product'])
        self.assertEqual(self._product_color.color, self._test_data['color'])
        self.assertEqual(self._product_color.display_color_name, self._test_data['display_color_name'])
    
    def test_display_color_name(self):
        self._test_data.pop('display_color_name')
        product_color = self._get_model_after_creation()

        self.assertEqual(product_color.display_color_name, product_color.color.name)


class ProductColorImagesTest(ModelTestCase):
    _model_class = ProductColorImages

    def setUp(self):
        product_color = ProductColorFactory()
        
        self._test_data = {
            'product_color': product_color,
            'image_url': 'product/color/product_1.jpg',
            'sequence': 1,
        }

    def test_create(self):
        product_color_images = self._get_model_after_creation()

        self.assertEqual(product_color_images.product_color, self._test_data['product_color'])
        self.assertEqual(product_color_images.image_url, self._test_data['image_url'])
        self.assertEqual(product_color_images.sequence, self._test_data['sequence'])


class SizeTest(ModelTestCase):
    _model_class = Size

    def setUp(self):
        self._test_data = {
            'name': 'XS',
        }

    def test_create(self):
        size = self._get_model_after_creation()

        self.assertEqual(size.name, self._test_data['name'])


class OptionTest(ModelTestCase):
    _model_class = Option

    # @classmethod
    # def setUpTestData(cls):
        

        
    #     cls._option = cls._get_default_model_after_creation()

    def setUp(self):
        product_color = ProductColorFactory()
        size = SizeFactory()
        self._test_data = {
            'product_color': product_color,
            'size': size,
            'display_size_name': '6호',
            'price_difference': 1500,
        }

    def test_create(self):
        option = self._get_model_after_creation()
        self.assertEqual(option.product_color, self._test_data['product_color'])
        self.assertEqual(option.size, self._test_data['size'])
        self.assertEqual(option.display_size_name, self._test_data['display_size_name'])
        self.assertEqual(option.price_difference, self._test_data['price_difference'])

    def test_display_size_name(self):
        self._test_data.pop('display_size_name')
        option = self._get_model_after_creation()

        self.assertEqual(option.display_size_name, option.size.name)

    def test_default_price_difference(self):
        self._test_data.pop('price_difference')
        option = self._get_model_after_creation()

        self.assertEqual(option.price_difference, 0)


class KeywordTest(ModelTestCase):
    _model_class = Keyword

    def setUp(self):
        self._test_data = {
            'name': '키워드',
        }

    def test_create(self):
        keyword = self._get_model_after_creation()

        self.assertEqual(keyword.name, self._test_data['name'])


class StyleTest(ModelTestCase):
    _model_class = Style

    def setUp(self):
        self._test_data = {
            'name': '로맨틱',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class LaundryInformationTest(ModelTestCase):
    _model_class = LaundryInformation

    def setUp(self):
        self._test_data = {
            'name': '다림질 금지',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class MaterialTest(ModelTestCase):
    _model_class = Material

    def setUp(self):
        self._test_data = {
            'name': '나일론',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class ProductMaterialTest(ModelTestCase):
    _model_class = ProductMaterial

    def setUp(self):
        product = ProductFactory()

        self._test_data = {
            'product': product,
            'material': '가죽',
            'mixing_rate': 75,
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.product, self._test_data['product'])
        self.assertEqual(style.material, self._test_data['material'])
        self.assertEqual(style.mixing_rate, self._test_data['mixing_rate'])
