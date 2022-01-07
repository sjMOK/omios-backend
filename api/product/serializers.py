from rest_framework.serializers import ModelSerializer
from . import models

class CategorySerializer(ModelSerializer):
    class Meta:
        model = models.Category
        fields = '__all__'


class SubCategorySerializer(ModelSerializer):
    class Meta:
        model = models.SubCategory
        exclude = ['category']


class ProductSerializer(ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'
