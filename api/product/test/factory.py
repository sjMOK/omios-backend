import random

from factory import Sequence, LazyAttribute, SubFactory, Faker, lazy_attribute
from factory.django import DjangoModelFactory

from user.test.factory import WholesalerFactory


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

    name = Sequence(lambda num: 'thickness_{0}'.format(num))
    

class SeeThroughFactory(DjangoModelFactory):
    class Meta:
        model = 'product.SeeThrough'

    name = Sequence(lambda num: 'age_{0}'.format(num))


class FlexibilityFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Flexibility'

    name = Sequence(lambda num: 'flexibility_{0}'.format(num))


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Product'

    wholesaler = SubFactory(WholesalerFactory)
    sub_category = SubFactory(SubCategoryFactory)
    style = SubFactory(StyleFactory)
    age = SubFactory(AgeFactory)
    name = Sequence(lambda num: 'product_{0}'.format(num))
    price = 35000
    thickness = SubFactory(ThicknessFactory)
    see_through = SubFactory(SeeThroughFactory)
    flexibility = SubFactory(FlexibilityFactory)
    lining = True


class TagFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Tag'

    name = Sequence(lambda num: 'tag_{0}'.format(num))


class ColorFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Color'

    name = Sequence(lambda num: 'color_{0}'.format(num))
    image_url = 'color/black.svg'


class SizeFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Size'

    name = Sequence(lambda num: 'size_{0}'.format(num))


class ProductColorFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductColor'

    product = SubFactory(ProductFactory)
    color = SubFactory(ColorFactory)
    display_color_name = Faker('color_name')
    image_url = 'product/sample/product_21.jpg'


class OptionFactory(DjangoModelFactory):
    class Meta:
        model = 'product.option'

    product_color = SubFactory(ProductColorFactory)
    size = Sequence(lambda num: 'size_{0}'.format(num))

    @lazy_attribute
    def price_difference(self):
        price = self.product_color.product.price
        price_difference = price * random.uniform(0, 0.2)

        cnt = 0
        while price_difference > 10:
            price_difference //= 10
            cnt += 1

        return price_difference * (10 ** cnt)


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
    material = Sequence(lambda num: 'material{0}'.format(num))
    mixing_rate = 100


class ProductImagesFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductImages'

    product = SubFactory(ProductFactory)
    image_url = 'product/sample/product_1.jpg'
    sequence = Sequence(lambda num: num)
