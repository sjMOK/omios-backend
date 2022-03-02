from rest_framework.serializers import (
    Serializer, ModelSerializer, ListSerializer, IntegerField, CharField, ImageField,
    PrimaryKeyRelatedField, URLField, DateTimeField, BooleanField,
)
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError, APIException

from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL
from common.serializers import DynamicFieldsSerializer, convert_primary_key_related_field_to_serializer
from .validators import validate_url, validate_price_difference
from .models import (
    LaundryInformation, ProductLaundryInformation, SubCategory, MainCategory, Color, Size, Option, Tag, Product, ProductImages,
    Style, Age, ProductAdditionalInformation, Thickness, SeeThrough, Flexibility, ProductMaterial,
    ProductColor, ProductColorImages,
)


class SubCategorySerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True, max_length=20)


class MainCategorySerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True, max_length=20, validators=[UniqueValidator(queryset=MainCategory.objects.all())])
    image_url = ImageField(read_only=True, max_length=200)
    sub_category = SubCategorySerializer(read_only=True, many=True, source='sub_categories')


class ColorSerializer(ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'


class SizeSerializer(ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'


class TagSerializer(Serializer):
    name = CharField(read_only=True, max_length=20)


class ProductImagesListSerializer(ListSerializer):
    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        sequence = 1
        for image_data in ret:
            image_data['sequence'] = sequence
            sequence += 1

        return ret

    def validate(self, attrs):
        urls = [attr.get('image_url') for attr in attrs]
        if len(urls) != len(set(urls)):
            raise ValidationError('product image_url is duplicated.')

        return attrs

class ProductImagesSerializer(Serializer):
    image_url = URLField(max_length=200)
    sequence = IntegerField(read_only=True, max_value=5, min_value=1)

    class Meta:
        list_serializer_class = ProductImagesListSerializer

    def validate_image_url(self, value):
        return validate_url(value)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class ProductColorImagesListSerializer(ListSerializer):
    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        
        sequence = 1
        for image_data in ret:
            image_data['sequence'] = sequence
            sequence += 1

        return ret

    def validate(self, attrs):
        urls = [attr.get('image_url') for attr in attrs]
        if len(urls) != len(set(urls)):
            raise ValidationError('product_color image_url is duplicated.')

        return attrs


class ProductColorImagesSerializer(Serializer):
    image_url = CharField(max_length=200)
    sequence = IntegerField(read_only=True, max_value=5, min_value=1)
    
    class Meta:
        list_serializer_class = ProductColorImagesListSerializer

    def validate_image_url(self, value):
        return validate_url(value)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class LaundryInformationSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True, max_length=20)


class ProductAdditionalInformationSerializer(Serializer):
    thickness = PrimaryKeyRelatedField(write_only=True, queryset=Thickness.objects.all())
    see_through = PrimaryKeyRelatedField(write_only=True, queryset=SeeThrough.objects.all())
    flexibility = PrimaryKeyRelatedField(write_only=True, queryset=Flexibility.objects.all())
    lining = BooleanField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        ret['thickness'] = ThicknessSerializer(instance.thickness).data
        ret['see_through'] = SeeThroughSerializer(instance.see_through).data
        ret['flexibility'] = FlexibilitySerializer(instance.flexibility).data

        return ret


class ProductMaterialListSerializer(ListSerializer):
    def validate(self, attrs):
        total_mixing_rate = sum([attr.get('mixing_rate') for attr in attrs])
        if total_mixing_rate > 100:
            raise ValidationError('The sum of the mixing_rate cannot exceed 100.')

        materials = [attr.get('material') for attr in attrs]
        if len(materials) != len(set(materials)):
            raise ValidationError('material is duplicated.')

        return attrs


class ProductMaterialSerializer(Serializer):
    id = IntegerField(read_only=True)
    material = CharField(max_length=20)
    mixing_rate = IntegerField(max_value=100, min_value=1)

    class Meta:
        list_serializer_class = ProductMaterialListSerializer


class OptionListSerializer(ListSerializer):
    def validate(self, attrs):
        sizes = [attr.get('size') for attr in attrs]
        if len(sizes) != len(set(sizes)):
            raise ValidationError("'size' is duplicated.")

        return attrs


class OptionSerializer(Serializer):
    id = IntegerField(read_only=True)
    display_size_name = CharField(allow_null=True, max_length=20)
    price_difference = IntegerField(max_value=100000, min_value=0, required=False)
    size = PrimaryKeyRelatedField(write_only=True, allow_null=True, queryset=Size.objects.all())

    class Meta:
        list_serializer_class = OptionListSerializer

    def validate(self, attrs):
        size = attrs.get('size')
        display_size_name = attrs.get('display_size_name')

        if size is None and display_size_name is None:
            raise ValidationError(
                "'size' and 'display_size_name' cannot be null values at the same time."
            )

        return attrs


class ProductColorListSerializer(ListSerializer):
    def validate(self, attrs):
        display_color_names = [attr.get('display_color_name') for attr in attrs]
        if len(display_color_names) != len(set(display_color_names)):
            raise ValidationError("'display color name' is duplicated.")

        return attrs


class ProductColorSerializer(Serializer):
    display_color_name = CharField(allow_null=True, max_length=20)
    color = PrimaryKeyRelatedField(queryset=Color.objects.all())
    options = OptionSerializer(allow_empty=False, many=True)
    images = ProductColorImagesSerializer(allow_empty=False, many=True)

    class Meta:
        list_serializer_class = ProductColorListSerializer

    def validate(self, attrs):
        display_color_name = attrs.get('display_color_name')
        if display_color_name is None:
            attrs['display_color_name'] = attrs.get('color').name
        
        return attrs


class AgeSerializer(Serializer):
    name = CharField(max_length=10, read_only=True)


class StyleSerializer(Serializer):
    name = CharField(max_length=20, read_only=True)


class ProductSerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=60)
    price = IntegerField(max_value=1000000, min_value=0)
    main_category = MainCategorySerializer(read_only=True, source='sub_category.main_category', allow_fields=('id', 'name'))
    sub_category = SubCategorySerializer(read_only=True)
    style = StyleSerializer(read_only=True)
    age = AgeSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    laundry_informations = LaundryInformationSerializer(read_only=True, many=True)
    product_additional_information = ProductAdditionalInformationSerializer()
    materials = ProductMaterialSerializer(allow_empty=False, many=True)
    colors = ProductColorSerializer(allow_empty=False, many=True)
    images = ProductImagesSerializer(allow_empty=False, many=True, source='related_images')

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if self.context['detail']:
            ret = self.to_representation_retrieve(ret, instance)
        else:
            ret['main_image'] = (BASE_IMAGE_URL + instance.related_images[0].image_url) if instance.related_images else DEFAULT_IMAGE_URL

        return ret

    def to_representation_retrieve(self, ret, instance):
        if not instance.related_images:
            ret['images'] = [DEFAULT_IMAGE_URL]

        return ret


class ProductWriteSerializer(ProductSerializer):
    sub_category = PrimaryKeyRelatedField(write_only=True, queryset=SubCategory.objects.all())
    style = PrimaryKeyRelatedField(write_only=True, queryset=Style.objects.all())
    age = PrimaryKeyRelatedField(write_only=True, queryset=Age.objects.all())
    tags = PrimaryKeyRelatedField(write_only=True, many=True, queryset=Tag.objects.all())
    laundry_informations = PrimaryKeyRelatedField(write_only=True, many=True, queryset=LaundryInformation.objects.all())

    def validate(self, attrs):
        price = attrs.get('price')
        
        product_colors = attrs.get('colors', list())
        for product_color in product_colors:
            options = product_color.get('options')
            validate_price_difference(price, options)

        return attrs

    def create(self, validated_data):
        laundry_informations = validated_data.pop('laundry_informations', list())
        tags = validated_data.pop('tags', list())
        product_additional_information = validated_data.pop('product_additional_information')
        materials = validated_data.pop('materials')
        colors = validated_data.pop('colors')
        images = validated_data.pop('related_images')

        product = Product.objects.create(wholesaler=self.context['wholesaler'], **validated_data)

        Product.laundry_informations.through.objects.bulk_create(
            [ProductLaundryInformation(product=product, laundry_information=laundry_information) for laundry_information in laundry_informations],
            ignore_conflicts=True
        )
        
        product.tags.add(*tags)

        ProductAdditionalInformation.objects.create(product=product, **product_additional_information)

        ProductMaterial.objects.bulk_create(
            [ProductMaterial(product=product, **material_data) for material_data in materials]
        )

        for color_data in colors:
            product_color_images = color_data.pop('images')
            options = color_data.pop('options')

            product_color = ProductColor.objects.create(product=product, **color_data)

            ProductColorImages.objects.bulk_create(
                [ProductColorImages(product_color=product_color, **product_color_image_data) for product_color_image_data in product_color_images]
            )

            for option_data in options:
                if option_data.get('display_size_name') is None:
                    option_data['display_size_name'] = option_data.get('size').name

            Option.objects.bulk_create(
                [Option(product_color=product_color, **option_data) for option_data in options]
            )

        ProductImages.objects.bulk_create(
            [ProductImages(product=product, **image_data) for image_data in images]
        )

        return product

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class MaterialSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20, read_only=True)


class ThicknessSerializer(Serializer):
    name = CharField(max_length=10, read_only=True)


class SeeThroughSerializer(Serializer):
    name = CharField(max_length=10, read_only=True)


class FlexibilitySerializer(Serializer):
    name = CharField(max_length=10, read_only=True)
