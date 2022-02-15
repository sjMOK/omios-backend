from factory import Sequence, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from common.factory import WholesalerFactory
from ..models import SubCategory

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = 'product.Product'

    name = '크로커다일레이디 크로커다일 베이직플리스점퍼 cl0wpf903'
    price = 35000
    wholesaler = SubFactory(WholesalerFactory)
