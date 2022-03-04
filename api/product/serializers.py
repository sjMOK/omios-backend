from rest_framework.serializers import (
    Serializer, ModelSerializer, ListSerializer, IntegerField, CharField, ImageField,
    PrimaryKeyRelatedField, URLField, BooleanField,
)
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError

from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL
from common.serializers import DynamicFieldsSerializer, convert_primary_key_related_field_to_serializer
from .validators import validate_url, validate_price_difference
from .models import (
    LaundryInformation, ProductLaundryInformation, SubCategory, MainCategory, Color, Size, Option, Tag, Product, 
    ProductImages, Style, Age, Thickness, SeeThrough, Flexibility, ProductMaterial, ProductColor,
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
    def validate(self, attrs):
        urls = []
        sequences = []
        for attr in attrs:
            if not(len(attr)==1 and 'id' in attr):
                urls.append(attr['image_url'])
                sequences.append(attr['sequence'])

        if len(urls) < 1:
            raise ValidationError(
            'The number of requested data is different from the number of materials the product has.')

        if has_duplicate_element(urls):
            raise ValidationError('Product image_url is duplicated.')

        sequences.sort()
        for index, value in enumerate(sequences):
            if value != (index+1):
                raise ValidationError(
                    'The sequence of the images must be ascending from 1 to n.'
                )

        return attrs


class ProductImagesSerializer(Serializer):
    id = IntegerField(required=False)
    image_url = URLField(max_length=200)
    sequence = IntegerField()

    class Meta:
        list_serializer_class = ProductImagesListSerializer

    def validate(self, attrs):
        if self.root.partial:
            if not bool(attrs):
                raise ValidationError('Product Image data is empty')
            if 'id' not in attrs:
                validate_create_data_in_partial_update(attrs, self.fields)

        return attrs

    def validate_image_url(self, value):
        return validate_url(value)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class LaundryInformationSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True, max_length=20)


class ThicknessSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)


class SeeThroughSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)


class FlexibilitySerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=10, read_only=True)


class ProductMaterialListSerializer(ListSerializer):
    def validate(self, attrs):
        total_mixing_rate = sum(
            [attr['mixing_rate'] for attr in attrs if not (len(attr)==1 and 'id' in attr)]
        )

        if total_mixing_rate != 100:
            raise ValidationError('The total of material mixing rates must be 100.')

        materials = [attr.get('material') for attr in attrs]
        if has_duplicate_element(materials):
            raise ValidationError('material is duplicated.')

        return attrs


class ProductMaterialSerializer(Serializer):
    id = IntegerField(required=False)
    material = CharField(max_length=20)
    mixing_rate = IntegerField(max_value=100, min_value=1)

    class Meta:
        list_serializer_class = ProductMaterialListSerializer

    def validate(self, attrs):
        if self.root.partial:
            if not bool(attrs):
                raise ValidationError('Product Material data is empty')
            if 'id' not in attrs:
                validate_create_data_in_partial_update(attrs, self.fields)

        return attrs


class OptionListSerializer(ListSerializer):
    def validate(self, attrs):
        sizes = [attr.get('size') for attr in attrs]
        if has_duplicate_element(sizes):
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

        image_urls = [attr.get('image_url') for attr in attrs]
        if len(image_urls) != len(set(image_urls)):
            raise ValidationError("'image_url' is duplicated.")

        return attrs


class ProductColorSerializer(Serializer):
    display_color_name = CharField(allow_null=True, max_length=20)
    color = PrimaryKeyRelatedField(queryset=Color.objects.all())
    options = OptionSerializer(allow_empty=False, many=True)
    image_url = CharField(max_length=200)

    class Meta:
        list_serializer_class = ProductColorListSerializer

    def validate(self, attrs):
        display_color_name = attrs.get('display_color_name')
        if display_color_name is None:
            attrs['display_color_name'] = attrs.get('color').name
        
        return attrs

    def validate_image_url(self, value):
        return validate_url(value)
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class AgeSerializer(Serializer):
    name = CharField(max_length=10, read_only=True)


class StyleSerializer(Serializer):
    name = CharField(max_length=20, read_only=True)


class ProductSerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=60)
    price = IntegerField(max_value=1000000, min_value=0)
    lining = BooleanField()
    materials = ProductMaterialSerializer(allow_empty=False, many=True)
    colors = ProductColorSerializer(allow_empty=False, many=True)
    images = ProductImagesSerializer(allow_empty=False, many=True, source='related_images')
    

class ProductReadSerializer(ProductSerializer):
    main_category = MainCategorySerializer(read_only=True, source='sub_category.main_category', allow_fields=('id', 'name'))
    sub_category = SubCategorySerializer(read_only=True)
    style = StyleSerializer(read_only=True)
    age = AgeSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    laundry_informations = LaundryInformationSerializer(read_only=True, many=True)
    thickness = ThicknessSerializer(read_only=True)
    see_through = SeeThroughSerializer(read_only=True)
    flexibility = FlexibilitySerializer(read_only=True)

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

        field_order = [
            'id', 'name', 'price', 'main_category', 'sub_category', 'style', 'age', 'tags', 
            'materials', 'laundry_informations', 'thickness', 'see_through', 'flexibility', 'lining', 'images', 'colors'
        ]

        for field in field_order:
            ret.move_to_end(field, last=True)

        return ret


class ProductWriteSerializer(ProductSerializer):
    sub_category = PrimaryKeyRelatedField( queryset=SubCategory.objects.all())
    style = PrimaryKeyRelatedField(queryset=Style.objects.all())
    age = PrimaryKeyRelatedField(queryset=Age.objects.all())
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    laundry_informations = PrimaryKeyRelatedField(many=True, queryset=LaundryInformation.objects.all())
    thickness = PrimaryKeyRelatedField(queryset=Thickness.objects.all())
    see_through = PrimaryKeyRelatedField( queryset=SeeThrough.objects.all())
    flexibility = PrimaryKeyRelatedField(queryset=Flexibility.objects.all())

    def validate(self, attrs):
        price = attrs.get('price')
        
        product_colors = attrs.get('colors', list())
        for product_color in product_colors:
            options = product_color.get('options')
            validate_price_difference(price, options)

        return attrs

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        field_order = [
            'id', 'name', 'price', 'sub_category', 'style', 'age', 'tags', 
            'materials', 'laundry_informations', 'thickness', 'see_through', 'flexibility', 'lining', 'images', 'colors'
        ]

        for field in field_order:
            ret.move_to_end(field, last=True)

        return ret
    

    def create(self, validated_data):
        laundry_informations = validated_data.pop('laundry_informations', list())
        tags = validated_data.pop('tags', list())
        materials = validated_data.pop('materials')
        colors = validated_data.pop('colors')
        images = validated_data.pop('related_images')

        product = Product.objects.create(wholesaler=self.context['wholesaler'], **validated_data)

        Product.laundry_informations.through.objects.bulk_create(
            [ProductLaundryInformation(product=product, laundry_information=laundry_information) for laundry_information in laundry_informations],
            ignore_conflicts=True
        )
        
        product.tags.add(*tags)

        ProductMaterial.objects.bulk_create(
            [ProductMaterial(product=product, **material_data) for material_data in materials]
        )

        for color_data in colors:
            options = color_data.pop('options')

            product_color = ProductColor.objects.create(product=product, **color_data)

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
        laundry_informations = validated_data.pop('laundry_informations', list())
        tags = validated_data.pop('tags', list())
        materials = validated_data.pop('materials', list())
        colors = validated_data.pop('colors', None)
        images = validated_data.pop('related_images', list())

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if materials:
            for material_data in materials:
                id = material_data.pop('id', None)

                if id is None:
                    ProductMaterial.objects.create(product=instance, **material_data)
                else:
                    product_material = ProductMaterial.objects.get(id=id)
                    for key, value in material_data.items():
                        setattr(product_material, key, value)

                    product_material.save()

        instance.save(update_fields=validated_data.keys())

        return instance


class MaterialSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20, read_only=True)
