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


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Product'

    name = Sequence(lambda num: 'product_{0}'.format(num))
    price = 35000
    wholesaler = SubFactory(WholesalerFactory)
    sub_category = SubFactory(SubCategoryFactory)


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


class OptionFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Option'

    product = SubFactory(ProductFactory)
    size = SubFactory(SizeFactory)
    color = SubFactory(ColorFactory)


class KeywordFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Keyword'

    name = Sequence(lambda num: 'keyword_{0}'.format(num))
