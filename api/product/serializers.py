import base64

from django.core.files.base import ContentFile

from rest_framework.serializers import *
from rest_framework.validators import UniqueValidator

from user.models import Wholesaler
from user.serializers import WholesalerSerializer
from . import models


class MainCategorySerializer(ModelSerializer):
    class Meta:
        model = models.MainCategory
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        
        return


class SubCategorySerializer(ModelSerializer):
    class Meta:
        model = models.SubCategory
        exclude = ['main_category']


class ColorSerializer(ModelSerializer):
    class Meta:
        model = models.Color
        fields = '__all__'

    
class SizeSerializer(ModelSerializer):
    class Meta:
        model = models.Size
        fields = '__all__'


class OptionSerializer(ModelSerializer):
    color = PrimaryKeyRelatedField(write_only=True, queryset=models.Color.objects.all())

    class Meta:
        model = models.Option
        exclude = ['product']

    def to_representation(self, instance):
        ret =  super().to_representation(instance)
        ret['size'] = instance.size.name
        ret['color'] = ret.pop('display_color_name')

        return ret


class ProductImagesSerializer(Serializer):
    id = IntegerField(read_only=True)
    url = ImageField(max_length=200)

    # class Meta:
    #     model = models.ProductImages
    #     fields = '__all__'


class ProductSerializer(ModelSerializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=60)
    code = CharField(read_only=True, max_length=12)
    created = DateTimeField(read_only=True, required=False)
    price = IntegerField(max_value=2147483647, min_value=-2147483648)
    sub_category = PrimaryKeyRelatedField(queryset=models.SubCategory.objects.all())
    options = OptionSerializer(many=True, source='related_options')
    images = ProductImagesSerializer(many=True, source='related_images')

    class Meta:
        model = models.Product
        exclude = ['wholesaler', 'on_sale']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        return

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if ret.get('images') is None and instance.related_images:
            ret['cover_image'] = instance.related_images[0].url.url

        if ret.get('sub_category'):
            ret['sub_category'] = SubCategorySerializer(instance.sub_category).data
            ret['main_category'] = MainCategorySerializer(instance.sub_category.main_category).data

        return ret

    def create(self, validated_data):
        options = validated_data.pop('related_options')
        images = validated_data.pop('related_images')

        product = models.Product.objects.create(wholesaler=self.context['wholesaler'], **validated_data)

        options = [models.Option(product=product, **option_data) for option_data in options ]
        models.Option.objects.bulk_create(options)

        for image_data in images:
            models.ProductImages.objects.create(product=product, **image_data)

        return product
