from rest_framework.serializers import *

from . import models, validators
from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL


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
    display_color_name = CharField(max_length=20, required=False)
    class Meta:
        model = models.Option
        exclude = ['product']

    def to_representation(self, instance):
        ret =  super().to_representation(instance)
        ret['size'] = instance.size.name
        ret['color'] = ret.pop('display_color_name')

        return ret

    def to_internal_value(self, data):
        ret =  super().to_internal_value(data)
        if ret.get('display_color_name', None) is None:
            ret['display_color_name'] = ret['color'].name

        return ret


class ProductImagesSerializer(Serializer):
    id = IntegerField(read_only=True)
    url = URLField(max_length=200)
    sequence = IntegerField(max_value=15, min_value=1)

    def validate_url(self, value):
        return validators.validate_url(value)


class ProductSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=60)
    code = CharField(max_length=12, read_only=True)
    created = DateTimeField(read_only=True)
    price = IntegerField(max_value=2147483647, min_value=0)
    sub_category = PrimaryKeyRelatedField(write_only=True, queryset=models.SubCategory.objects.all())
    options = OptionSerializer(many=True, source='related_options')
    images = ProductImagesSerializer(many=True, source='related_images')
    on_sale = BooleanField(required=False)


    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        return

    def to_representation_retrieve(self, ret, instance):
        ret['sub_category'] = SubCategorySerializer(instance.sub_category).data
        ret['main_category'] = MainCategorySerializer(instance.sub_category.main_category).data
            
        related_images = ret.get('images', None)
        if related_images:
            for image in related_images:
                image['url'] = BASE_IMAGE_URL + image['url']
        else:
            ret['images'] = [DEFAULT_IMAGE_URL]

        return ret

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if self.context['detail']:
            ret = self.to_representation_retrieve(ret, instance)
        else:
            ret['main_image'] = (BASE_IMAGE_URL + instance.related_images[0].url) if instance.related_images else DEFAULT_IMAGE_URL

        return ret

    def create(self, validated_data):
        related_options = validated_data.pop('related_options')
        related_images = validated_data.pop('related_images')

        product = models.Product.objects.create(wholesaler=self.context['wholesaler'], **validated_data)

        options = [models.Option(product=product, **option_data) for option_data in related_options ]
        models.Option.objects.bulk_create(options)

        images = [models.ProductImages(product=product, **image_data) for image_data in related_images]
        models.ProductImages.objects.bulk_create(images)

        return product
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)



class ImageSerializer(Serializer):
    image = ImageField(max_length=200, validators=[validators.validate_file_size])
