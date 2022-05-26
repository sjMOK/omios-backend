import string, random

from django.utils import timezone

from factory import Sequence, LazyAttribute, SubFactory, Faker, LazyFunction, lazy_attribute

from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyInteger

from common.utils import IMAGE_DATETIME_FORMAT
from user.test.factories import WholesalerFactory, ShopperFactory


def create_options(size=2, only_product_color=False):
    option = OptionFactory()

    if only_product_color:
        return [option] + [OptionFactory(product_color=option.product_color) for _ in range(size-1)]
    else:
        return [option] + [OptionFactory(product_color__product=ProductFactory(product=option.product_color.product)) for _ in range(size-1)]


class MainCategoryFactory(DjangoModelFactory):
    class Meta:
        model = 'product.MainCategory'

    name = Sequence(lambda num: 'main_category_{0}'.format(num))
    image_url = LazyAttribute(lambda obj: 'category/{0}.svg'.format(obj.name))


class SubCategoryFactory(DjangoModelFactory):
    class Meta:
        model = 'product.SubCategory'

    main_category = SubFactory(MainCategoryFactory)
    name = Sequence(lambda num: 'sub_category_{0}'.format(num))
    require_product_additional_information = True
    require_laundry_information = True


class StyleFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Style'

    name = Sequence(lambda num: 'test_style_{0}'.format(num))


class AgeFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Age'

    name = name = Sequence(lambda num: 'age_{0}'.format(num))


class ThicknessFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Thickness'

    name = Sequence(lambda num: 'thick_{0}'.format(num))
    

class SeeThroughFactory(DjangoModelFactory):
    class Meta:
        model = 'product.SeeThrough'

    name = Sequence(lambda num: 'see_th_{0}'.format(num))


class FlexibilityFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Flexibility'

    name = Sequence(lambda num: 'flex_{0}'.format(num))


class ThemeFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Theme'
    
    name = Sequence(lambda num: 'theme_{0}'.format(num))


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Product'

    wholesaler = SubFactory(WholesalerFactory)
    sub_category = SubFactory(SubCategoryFactory)
    style = SubFactory(StyleFactory)
    age = SubFactory(AgeFactory)
    name = Sequence(lambda num: 'product_{0}'.format(num))
    price = FuzzyInteger(10000, 5000000, 100)
    sale_price = LazyAttribute(lambda obj: obj.price * 2)
    base_discount_rate = FuzzyInteger(0, 50)
    base_discounted_price = LazyAttribute(lambda obj: obj.sale_price - int(obj.sale_price * obj.base_discount_rate / 100) // 100 * 100)
    thickness = SubFactory(ThicknessFactory)
    see_through = SubFactory(SeeThroughFactory)
    flexibility = SubFactory(FlexibilityFactory)
    lining = True
    manufacturing_country = Faker('country', locale='ko-KR')
    theme = SubFactory(ThemeFactory)
        
    @classmethod
    def _generate(cls, strategy, params):
        if 'product' in params:
            product = params.pop('product')
            copy_fields = ['wholesaler', 'sub_category', 'style', 'age', 'thickness', 'see_through', 'flexibility', 'theme']
            for field in copy_fields:
                if field not in params:
                    params[field] = getattr(product, field, None)

        return super()._generate(strategy, params)


class TagFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Tag'

    name = Sequence(lambda num: 'tag_{0}'.format(num))


class ColorFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Color'

    name = Sequence(lambda num: 'color_{0}'.format(num))
    image_url = LazyAttribute(lambda obj: 'color/{0}.svg'.format(obj.name))


class SizeFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Size'

    name = Sequence(lambda num: 'size{0}'.format(num))


class ProductColorFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductColor'

    product = SubFactory(ProductFactory)
    color = SubFactory(ColorFactory)
    image_url = LazyFunction(lambda: '{}.jpeg'.format(timezone.now().strftime(IMAGE_DATETIME_FORMAT)))
    display_color_name = Sequence(lambda num: 'dp_name_{0}'.format(num))


class OptionFactory(DjangoModelFactory):
    class Meta:
        model = 'product.option'

    product_color = SubFactory(ProductColorFactory)
    size = Sequence(lambda num: 'size{0}'.format(num))


class LaundryInformationFactory(DjangoModelFactory):
    class Meta:
        model = 'product.LaundryInformation'

    name = Sequence(lambda num: 'laundry_info_{0}'.format(num))


class MaterialFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Material'

    name = Sequence(lambda num: 'material{0}'.format(num))


class ProductMaterialFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductMaterial'

    product = SubFactory(ProductFactory)
    mixing_rate = 100

    @lazy_attribute
    def material(self):
        string_length = 10
        return ''.join(random.sample(string.ascii_letters, string_length))


class ProductImageFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductImage'

    product = SubFactory(ProductFactory)
    image_url = LazyFunction(lambda: '{}.jpeg'.format(timezone.now().strftime(IMAGE_DATETIME_FORMAT)))
    sequence = Sequence(lambda num: num)


class KeyWordFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Keyword'

    name = Sequence(lambda num: 'keyword_{0}'.format(num))


class ProductQuestionAnswerClassificationFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductQuestionAnswerClassification'

    name = Sequence(lambda num: 'classification_{0}'.format(num))


class ProductQuestionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductQuestionAnswer'

    product = SubFactory(ProductFactory)
    shopper = SubFactory(ShopperFactory)
    classification = SubFactory(ProductQuestionAnswerClassificationFactory)
    question = Faker('sentence')
    answer = Faker('sentence')
    is_secret = Faker('pybool')
