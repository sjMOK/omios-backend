from factory import Sequence, LazyAttribute, SubFactory
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


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Product'

    name = Sequence(lambda num: 'product_{0}'.format(num))
    price = 35000
    wholesaler = SubFactory(WholesalerFactory)
    sub_category = SubFactory(SubCategoryFactory)
    style = SubFactory(StyleFactory)
    age = SubFactory(AgeFactory)


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


class TagFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Tag'

    name = Sequence(lambda num: 'tag_{0}'.format(num))


class ColorFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Color'

    name = Sequence(lambda num: 'color_{0}'.format(num))
    image_url = 'color/black.svg'


class ProductColorFactory(DjangoModelFactory):
    class Meta:
        model = 'product.ProductColor'

    product = SubFactory(ProductFactory)
    color = SubFactory(ColorFactory)
    display_color_name = Sequence(lambda num: 'display_color_name_{0}'.format(num))


class SizeFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Size'

    name = Sequence(lambda num: 'size_{0}'.format(num))


class LaundryInformationFactory(DjangoModelFactory):
    class Meta:
        model = 'product.LaundryInformation'

    name = Sequence(lambda num: 'laundry_info_{0}'.format(num))
