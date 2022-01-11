from rest_framework.serializers import *
from . import models


class MainCategorySerializer(ModelSerializer):
    class Meta:
        model = models.MainCategory
        fields = '__all__'


class SubCategorySerializer(ModelSerializer):
    class Meta:
        model = models.SubCategory
        exclude = ['main_category']


class ColorSerializer(ModelSerializer):
    class Meta:
        model = models.Color
        fields = '__all__'


class ProductSerializer(ModelSerializer):
    code = CharField(max_length=12, read_only=True)
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


class ProductImagesSerializer(ModelSerializer):
    class Meta:
        model = models.ProductImages
        fields = '__all__'
