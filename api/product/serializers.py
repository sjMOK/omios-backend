from rest_framework.serializers import *
from . import models
from user.models import Wholesaler


class MainCategorySerializer(ModelSerializer):
    class Meta:
        model = models.MainCategory
        fields = '__all__'


class SubCategorySerializer(ModelSerializer):
    class Meta:
        model = models.SubCategory
        exclude = ['main_category']


class ProductSerializer(ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'


class ProductShopperListSerializer(ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'


class ProductWholesalerListSerializer(ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'
