from django.test import tag

from freezegun import freeze_time
from datetime import datetime
from pdb import set_trace

from common.test.test_cases import ModelTestCase, FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from user.test.factory import WholesalerFactory
from ..models import *
from .factory import (
    MainCategoryFactory, SubCategoryFactory, ProductFactory, 
    TagFactory, SizeFactory, ColorFactory
)



class MainCategoryTest(ModelTestCase):
    _model_class = MainCategory
    
    def setUp(self):
        self._test_data = {
            'name': '아우터',
            'image_url': 'category/outer.svg'
        }

    def test_create(self):
        main_category = self._get_model_after_creation()
        
        self.assertEqual(main_category.name, self._test_data['name'])
        self.assertEqual(main_category.image_url.name, self._test_data['image_url'])


class SubCategoryTest(ModelTestCase):
    _model_class = SubCategory

    @classmethod
    def setUpTestData(cls):
        cls.main_category = MainCategoryFactory()

    def setUp(self):
        self._test_data = {
            'main_category': self.main_category,
            'name': '가디건'
        }

    def test_create(self):
        sub_category = self._get_model_after_creation()
        
        self.assertEqual(sub_category.name, self._test_data['name'])
        self.assertEqual(sub_category.main_category, self._test_data['main_category'])


class ProductTest(ModelTestCase):
    _model_class = Product

    @classmethod
    def setUpTestData(cls):
        cls.wholesaler = WholesalerFactory(username='musinsa')
        cls.sub_category = SubCategoryFactory()

    def setUp(self):
        self._test_data = {
            'name': '크로커다일레이디 크로커다일 베이직플리스점퍼 cl0wpf903',
            'sub_category': self.sub_category,
            'price': 35000,
            'wholesaler': self.wholesaler
        }

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create(self):
        self._test_data['sub_category'].name = '테스트'
        self._test_data['sub_category'].save()
        
        product = self._get_model_after_creation()

        self.assertEqual(product.name, self._test_data['name'])
        self.assertEqual(product.code, 'AA')
        self.assertEqual(product.sub_category, self._test_data['sub_category'])
        self.assertEqual(product.created, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(product.price, self._test_data['price'])
        self.assertEqual(product.wholesaler, self._test_data['wholesaler'])
        self.assertTrue(product.on_sale)


class ProductImagesTest(ModelTestCase):
    _model_class = ProductImages

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()

    def setUp(self):
        self._test_data = {
            'product': self.product,
            'url': 'product/sample/product_5.jpg',
            'sequence': 1
        }

    def test_create(self):
        product_image = self._get_model_after_creation()

        self.assertEqual(product_image.product, self._test_data['product'])
        self.assertEqual(product_image.url, self._test_data['url'])
        self.assertEqual(product_image.sequence, self._test_data['sequence'])


class TagTest(ModelTestCase):
    _model_class = Tag

    def setUp(self):
        self._test_data = {'name': '남친룩'}

    def test_create(self):
        tag = self._get_model_after_creation()

        self.assertEqual(tag.name, self._test_data['name'])


class ProductTagTest(ModelTestCase):
    _model_class = ProductTag

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.tag = TagFactory()

    def setUp(self):
        self._test_data = {
            'product': self.product,
            'tag': self.tag
        }

    def test_create(self):
        product_tag = self._get_model_after_creation()

        self.assertEqual(product_tag.product, self._test_data['product'])
        self.assertEqual(product_tag.tag, self._test_data['tag'])
        

class ColorTest(ModelTestCase):
    _model_class = Color

    def setUp(self):
        self._test_data = {
            'name': '블랙',
            'image_url': 'color/black.svg'
        }

    def test_create(self):
        color = self._get_model_after_creation()

        self.assertEqual(color.name, self._test_data['name'])
        self.assertEqual(color.image_url.name, self._test_data['image_url'])


class SizeTest(ModelTestCase):
    _model_class = Size

    def setUp(self):
        self._test_data = {'name': 'XS'}

    def test_create(self):
        size = self._get_model_after_creation()

        self.assertEqual(size.name, self._test_data['name'])


class OptionTest(ModelTestCase):
    _model_class = Option

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.size = SizeFactory()
        cls.color = ColorFactory()

    def setUp(self):
        self._test_data = {
            'product': self.product,
            'size': self.size,
            'color': self.color,
            'display_color_name': '다크',
            'price_difference': 1500
        }

    def test_create(self):
        option = self._get_model_after_creation()

        self.assertEqual(option.product, self._test_data['product'])
        self.assertEqual(option.size, self._test_data['size'])
        self.assertEqual(option.color, self._test_data['color'])
        self.assertEqual(option.display_color_name, self._test_data['display_color_name'])
        self.assertEqual(option.price_difference, self._test_data['price_difference'])

    def test_default_values(self):
        option = self._get_model_after_creation()
        option.display_color_name = ''
        option.save()
        
        self.assertEqual(option.display_color_name, option.color.name)

        self._test_data.pop('display_color_name')
        self._test_data.pop('price_difference')
        option = self._get_model_after_creation()

        self.assertEqual(option.display_color_name, option.color.name)
        self.assertEqual(option.price_difference, 0)


class KeywordTest(ModelTestCase):
    _model_class = Keyword

    def setUp(self):
        self._test_data = {
            'name': '키워드'
        }

    def test_create(self):
        keyword = self._get_model_after_creation()

        self.assertEqual(keyword.name, self._test_data['name'])
