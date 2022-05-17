from django.forms import model_to_dict

from freezegun import freeze_time

from common.test.test_cases import ModelTestCase, FREEZE_TIME, FREEZE_TIME_FORMAT, FREEZE_TIME_AUTO_TICK_SECONDS
from user.test.factories import WholesalerFactory, ShopperFactory
from ..models import (
    MainCategory, SubCategory, Product, Age, SubCategorySize, Thickness, SeeThrough, Flexibility, ProductImage,
    Tag, Color, ProductColor, Size, Option, Keyword, Style, LaundryInformation, Material, ProductMaterial, Theme,
    ProductQuestionAnswerClassification, ProductQuestionAnswer,
)
from .factories import (
    AgeFactory, MainCategoryFactory, OptionFactory, ProductQuestionAnswerFactory, StyleFactory, SubCategoryFactory, ProductFactory,
    ThemeFactory, ThicknessFactory, SeeThroughFactory, FlexibilityFactory, ColorFactory, ProductColorFactory, SizeFactory,
    ProductQuestionAnswerClassificationFactory,
)


class MainCategoryTestCase(ModelTestCase):
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


class SubCategoryTestCase(ModelTestCase):
    _model_class = SubCategory

    def setUp(self):
        self._test_data = {
            'main_category': MainCategoryFactory(),
            'name': '가디건',
            'require_product_additional_information': True,
            'require_laundry_information': True,
        }

    def test_create(self):
        sub_category = self._get_model_after_creation()
        
        self.assertEqual(sub_category.name, self._test_data['name'])
        self.assertEqual(sub_category.main_category, self._test_data['main_category'])
        self.assertEqual(
            sub_category.require_product_additional_information, 
            self._test_data['require_product_additional_information']
        )
        self.assertEqual(
            sub_category.require_laundry_information,
            self._test_data['require_laundry_information']
        )


class ProductTestCase(ModelTestCase):
    _model_class = Product

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            'wholesaler': WholesalerFactory(),
            'sub_category': SubCategoryFactory(),
            'name': '크로커다일레이디 크로커다일 베이직플리스점퍼 cl0wpf903',
            'price': 35000,
            'sale_price': 70000,
            'base_discount_rate': 10,
            'base_discounted_price': 63000,
            'style': StyleFactory(),
            'age': AgeFactory(),
            'thickness': ThicknessFactory(),
            'see_through': SeeThroughFactory(),
            'flexibility': FlexibilityFactory(),
            'lining': True,
            'manufacturing_country': '대한민국',
            'theme': ThemeFactory(),
        }

        cls._product = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertEqual(self._product.wholesaler, self._test_data['wholesaler'])
        self.assertEqual(self._product.name, self._test_data['name'])
        self.assertEqual(self._product.sub_category, self._test_data['sub_category'])
        self.assertEqual(self._product.price, self._test_data['price'])
        self.assertEqual(self._product.base_discount_rate, self._test_data['base_discount_rate'])
        self.assertEqual(self._product.age, self._test_data['age'])
        self.assertEqual(self._product.style, self._test_data['style'])
        self.assertEqual(self._product.thickness, self._test_data['thickness'])
        self.assertEqual(self._product.see_through, self._test_data['see_through'])
        self.assertEqual(self._product.flexibility, self._test_data['flexibility'])
        self.assertEqual(self._product.lining, self._test_data['lining'])
        self.assertEqual(self._product.manufacturing_country, self._test_data['manufacturing_country'])
        self.assertEqual(self._product.theme, self._test_data['theme'])

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create_default_values(self):
        self._test_data.pop('base_discount_rate')
        product = self._get_model_after_creation()

        self.assertEqual(product.base_discount_rate, 0)
        self.assertEqual(product.code, 'AA')
        self.assertTrue(product.on_sale)

    def test_delete(self):
        product_color = ProductColorFactory(product=self._product)
        OptionFactory(product_color=product_color)
        ProductQuestionAnswerFactory(product=self._product)
        self._product.delete()

        self.assertTrue(not self._product.on_sale)
        self.assertTrue(not self._product.colors.filter(on_sale=True).exists())
        self.assertTrue(not Option.objects.filter(product_color__product=self._product, on_sale=True).exists())
        self.assertTrue(not ProductQuestionAnswer.objects.all().exists())
        


class AgeTestCase(ModelTestCase):
    _model_class = Age

    def setUp(self):
        self._test_data = {
            'name': '20대 중반',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class ThicknessTestCase(ModelTestCase):
    _model_class = Thickness

    def setUp(self):
        self._test_data = {
            'name': '두꺼움',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class SeeThroughTestCase(ModelTestCase):
    _model_class = SeeThrough

    def setUp(self):
        self._test_data = {
            'name': '비침',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class FlexibilityTestCase(ModelTestCase):
    _model_class = Flexibility

    def setUp(self):
        self._test_data = {
            'name': '높음',
        }
    
    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])        


class ProductImagesTestCase(ModelTestCase):
    _model_class = ProductImage

    def setUp(self):
        self._test_data = {
            'product': ProductFactory(),
            'image_url': 'product/sample/product_5.jpg',
            'sequence': 1,
        }

    def test_create(self):
        product_image = self._get_model_after_creation()

        self.assertEqual(product_image.product, self._test_data['product'])
        self.assertEqual(product_image.image_url, self._test_data['image_url'])
        self.assertEqual(product_image.sequence, self._test_data['sequence'])


class TagTestCase(ModelTestCase):
    _model_class = Tag

    def setUp(self):
        self._test_data = {
            'name': '남친룩',
        }

    def test_create(self):
        tag = self._get_model_after_creation()

        self.assertEqual(tag.name, self._test_data['name'])
        

class ColorTestCase(ModelTestCase):
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


class ProductColorTestCase(ModelTestCase):
    _model_class = ProductColor

    @classmethod
    def setUpTestData(cls):
        cls._test_data = {
            'product': ProductFactory(),
            'color': ColorFactory(),
            'display_color_name': 'display_color_name',
            'image_url': 'product/sample/product_21.jpg'
        }

    def test_create(self):
        product_color = self._get_model_after_creation()
        self.assertEqual(product_color.product, self._test_data['product'])
        self.assertEqual(product_color.color, self._test_data['color'])
        self.assertEqual(product_color.display_color_name, self._test_data['display_color_name'])
        self.assertEqual(product_color.image_url, self._test_data['image_url'])
    
    def test_create_default_values(self):
        self._test_data.pop('display_color_name')
        product_color = self._get_model_after_creation()

        self.assertEqual(product_color.display_color_name, product_color.color.name)
        self.assertTrue(product_color.on_sale)


class SizeTestCase(ModelTestCase):
    _model_class = Size

    def setUp(self):
        self._test_data = {
            'name': 'XS',
        }

    def test_create(self):
        size = self._get_model_after_creation()

        self.assertEqual(size.name, self._test_data['name'])


class SubCategorySizeTestCase(ModelTestCase):
    _model_class = SubCategorySize

    def setUp(self):
        self._test_data = {
            'sub_category': SubCategoryFactory(),
            'size': SizeFactory(),
        }

    def test_create(self):
        sub_category_size = self._get_model_after_creation()

        self.assertEqual(sub_category_size.sub_category, self._test_data['sub_category'])
        self.assertEqual(sub_category_size.size, self._test_data['size'])


class OptionTestCase(ModelTestCase):
    _model_class = Option

    def setUp(self):
        self._test_data = {
            'product_color': ProductColorFactory(),
            'size': 'Free'
        }

    def test_create(self):
        option = self._get_model_after_creation()
        self.assertEqual(option.product_color, self._test_data['product_color'])
        self.assertEqual(option.size, self._test_data['size'])


class KeywordTestCase(ModelTestCase):
    _model_class = Keyword

    def setUp(self):
        self._test_data = {
            'name': '키워드',
        }

    def test_create(self):
        keyword = self._get_model_after_creation()

        self.assertEqual(keyword.name, self._test_data['name'])


class StyleTestCase(ModelTestCase):
    _model_class = Style
    
    def setUp(self):
        self._test_data = {
            'name': '로맨틱',
        }

    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class LaundryInformationTestCase(ModelTestCase):
    _model_class = LaundryInformation

    def setUp(self):
        self._test_data = {
            'name': '다림질 금지',
        }

    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class MaterialTestCase(ModelTestCase):
    _model_class = Material

    def setUp(self):
        self._test_data = {
            'name': '나일론',
        }

    def test_create(self):
        style = self._get_model_after_creation()

        self.assertEqual(style.name, self._test_data['name'])


class ProductMaterialTestCase(ModelTestCase):
    _model_class = ProductMaterial

    def setUp(self):
        self._test_data = {
            'product': ProductFactory(),
            'material': '가죽',
            'mixing_rate': 75,
        }

    def test_create(self):
        product_material = self._get_model_after_creation()

        self.assertEqual(product_material.product, self._test_data['product'])
        self.assertEqual(product_material.material, self._test_data['material'])
        self.assertEqual(product_material.mixing_rate, self._test_data['mixing_rate'])


class ThemeTestCase(ModelTestCase):
    _model_class = Theme

    def test_create(self):
        self._test_data = {
            'name': '파티룩',
        }
        theme = self._get_model_after_creation()

        self.assertEqual(theme.name, self._test_data['name'])



class ProductQuestionAnswerClassificationTestCase(ModelTestCase):
    _model_class = ProductQuestionAnswerClassification

    def setUp(self):
        self._test_data = {
            'name': '상품 문의',
        }

    def test_create(self):
        classification = self._get_model_after_creation()

        self.assertDictEqual(
            model_to_dict(classification, exclude='id'),
            self._test_data
        )


class ProductQuestionAnswerTestCase(ModelTestCase):
    _model_class = ProductQuestionAnswer

    @classmethod
    def setUpTestData(cls):
        cls.__default_fields = ('created_at', 'is_secret')
        cls._test_data = {
            'product': ProductFactory(),
            'shopper': ShopperFactory(),
            'classification': ProductQuestionAnswerClassificationFactory(),
            'question': 'question',
            'answer': 'answer'
        }
        cls._question_answer = cls._get_default_model_after_creation()

    def test_create(self):
        self.assertDictEqual(
            model_to_dict(self._question_answer, exclude=('id',) + self.__default_fields),
            {
                **self._test_data,
                'product': self._test_data['product'].id,
                'shopper': self._test_data['shopper'].user_id,
                'classification': self._test_data['classification'].id
            }
        )

    @freeze_time(FREEZE_TIME, auto_tick_seconds=FREEZE_TIME_AUTO_TICK_SECONDS)
    def test_create_default_value(self):
        self.assertTrue(not self._question_answer.is_secret)
