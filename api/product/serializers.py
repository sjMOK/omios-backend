from rest_framework.serializers import *
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
    subcategory_id = PrimaryKeyRelatedField(queryset=models.SubCategory.objects.all())
    class Meta:
        model = models.Product
        exclude = ['subcategory']
