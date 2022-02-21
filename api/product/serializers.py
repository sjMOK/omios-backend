from rest_framework.serializers import (
    Serializer, ModelSerializer, IntegerField, CharField, ImageField, PrimaryKeyRelatedField,
    URLField, DateTimeField, BooleanField,
)
from rest_framework.validators import UniqueValidator

from .validators import validate_file_size, validate_url
from .models import (
    SubCategory, MainCategory, Color, Size, Option, Tag, Product, ProductImages,
) 
from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL
from common.serializers import DynamicFieldSerializer


class SubCategorySerializer(DynamicFieldSerializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20)
    sizes = PrimaryKeyRelatedField(many=True, read_only=True)


class MainCategorySerializer(DynamicFieldSerializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20, validators=[UniqueValidator(queryset=MainCategory.objects.all())])
    image_url = ImageField(max_length=200)
    sub_category = SubCategorySerializer(many=True, allow_fields=('id', 'name'), source='sub_categories')


class ColorSerializer(ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

    
class SizeSerializer(ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'


class OptionSerializer(ModelSerializer):
    color = PrimaryKeyRelatedField(write_only=True, queryset=Color.objects.all())
    display_color_name = CharField(max_length=20, required=False)

    class Meta:
        model = Option
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


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class ProductImagesSerializer(Serializer):
    id = IntegerField(read_only=True)
    url = URLField(max_length=200)
    sequence = IntegerField(max_value=15, min_value=1)

    def validate_url(self, value):
        return validate_url(value)


class ProductSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=60)
    code = CharField(max_length=12, read_only=True)
    created = DateTimeField(read_only=True)
    price = IntegerField(max_value=2147483647, min_value=0)
    sub_category = PrimaryKeyRelatedField(write_only=True, queryset=SubCategory.objects.all())
    options = OptionSerializer(many=True, source='related_options')
    images = ProductImagesSerializer(many=True, source='related_images')
    tags = TagSerializer(many=True, source='related_tags')
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
        ret['tags'] = [tag['name'] for tag in ret['tags']]

        related_images = ret.get('images', None)
        if related_images is not None:
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

        product = Product.objects.create(wholesaler=self.context['wholesaler'], **validated_data)

        options = [Option(product=product, **option_data) for option_data in related_options ]
        Option.objects.bulk_create(options)

        images = [ProductImages(product=product, **image_data) for image_data in related_images]
        ProductImages.objects.bulk_create(images)

        return product
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class ImageSerializer(Serializer):
    image = ImageField(max_length=200, validators=[validate_file_size])


class LaundryInformationSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20)


class MaterialSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20, read_only=True)


class StyleSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20, read_only=True)


class AgeSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)


class ThicknessSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)


class SeeThroughSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)


class FlexibilitySerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)
