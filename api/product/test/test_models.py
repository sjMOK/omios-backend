from django.test import tag

from freezegun import freeze_time
from datetime import datetime

from common.storage import ClientSVGStorage
from common.test import ModelTestCase, FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from ..models import Product, MainCategory, SubCategory
from user.models import Wholesaler, Membership


class MainCategoryTest(ModelTestCase):
    _model_class = MainCategory
    

    def setUp(self):
        self.test_data = {
            'name': '아우터',
            'image_url': 'category/outer.svg'
        }

    def test_create(self):
        main_category = self._get_model_after_creation()
        
        self.assertEqual(main_category.name, self.test_data['name'])
        self.assertEqual(main_category.image_url.name, self.test_data['image_url'])
        self.assertIsInstance(main_category.image_url.storage, ClientSVGStorage)


class SubCategoryTest(ModelTestCase):
    fixtures = ['main_category']
    _model_class = SubCategory

    def setUp(self):
        main_category = MainCategory.objects.get(id=1)
        self.test_data = {
            'main_category': main_category,
            'name': '가디건'
        }

    def test_create(self):
        sub_category = self._get_model_after_creation()
        
        self.assertEqual(sub_category.name, self.test_data['name'])
        self.assertEqual(sub_category.main_category, self.test_data['main_category'])


class ProductTest(ModelTestCase):
    fixtures = ['main_category', 'sub_category']
    _model_class = Product

    @classmethod
    def setUpTestData(cls):
        wholesaler = Wholesaler.objects.create(
            username='musinsa', password='Ahrtmdwn123', name='무신사', email='musinsa@naver.com',
            phone='01011111111', company_registration_number=111122223333
        )
        sub_category = SubCategory.objects.get(id=1)

        cls.test_data = {
            'name': '크로커다일레이디 크로커다일 베이직플리스점퍼 cl0wpf903',
            'sub_category': sub_category,
            'price': 35000,
            'wholesaler': wholesaler
        }

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test(self):
        product = self._get_model_after_creation()
        
        self.assertEqual(product.name, self.test_data['name'])
        self.assertEqual(product.code, 'AA')
        self.assertEqual(product.sub_category, self.test_data['sub_category'])
        self.assertEqual(product.created, datetime.strptime(FREEZE_TIME, FREEZE_TIME_FORMAT))
        self.assertEqual(product.price, self.test_data['price'])
        self.assertEqual(product.wholesaler, self.test_data['wholesaler'])
        self.assertTrue(product.on_sale)
