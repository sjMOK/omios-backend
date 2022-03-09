from django.db.models import Manager

from rest_framework.serializers import (
    Serializer, ModelSerializer, ListSerializer, IntegerField, CharField, ImageField,
    PrimaryKeyRelatedField, URLField, BooleanField,
)
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError, APIException

from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL
from common.serializers import DynamicFieldsSerializer
from .validators import validate_url, validate_price_difference
from .models import (
    LaundryInformation, ProductLaundryInformation, SubCategory, MainCategory, Color, Size, Option, Tag, Product, 
    ProductImages, Style, Age, Thickness, SeeThrough, Flexibility, ProductMaterial, ProductColor,
)

def validate_require_data_in_partial_update(data, fields):
    for key, value in fields.items():
        if getattr(value, 'required', True) and key not in data:
            raise ValidationError('{0} field is required.'.format(key))

def has_duplicate_element(array):
    if len(array) != len(set(array)):
        return True
    return False

def is_delete_data(data):
    if len(data.keys())==1 and 'id' in data:
        return True
    return False

def is_update_data(data):
    if len(data.keys())>1 and 'id' in data:
        return True
    return False

def is_create_data(data):
    if bool(data) and 'id' not in data:
        return True
    return False


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


class AgeSerializer(Serializer):
    name = CharField(max_length=10, read_only=True)


class StyleSerializer(Serializer):
    name = CharField(max_length=20, read_only=True)


class ProductImagesListSerializer(ListSerializer):
    def validate(self, attrs):
        if self.root.instance is not None:
            update_or_delete_attrs_id = [attr.get('id') for attr in attrs if not is_create_data(attr)].sort()
            product_images_id = list(self.root.instance.images.all().order_by('id').values_list('id', flat=True))

            if update_or_delete_attrs_id != product_images_id:
                raise ValidationError(
                    'You must contain all image data that the product has.'
                )

        create_or_update_attrs = [attr for attr in attrs if not is_delete_data(attr)]
        if len(create_or_update_attrs) > 10:
            raise ValidationError(
                'The product cannot have more than ten images.'
            )
        elif len(create_or_update_attrs) == 0:
            raise ValidationError(
                'The product must have at least one image.'
            )

        urls = [attr['image_url'] for attr in create_or_update_attrs]
        sequences = [attr['sequence'] for attr in create_or_update_attrs]

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
        if self.root.partial and not is_delete_data(attrs):
            validate_require_data_in_partial_update(attrs, self.fields)

        return attrs

    def validate_image_url(self, value):
        return validate_url(value)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class ProductMaterialListSerializer(ListSerializer):
    def validate(self, attrs):
        total_mixing_rate = sum(
            [attr['mixing_rate'] for attr in attrs if not is_delete_data(attr)]
        )

        if total_mixing_rate != 100:
            raise ValidationError('The total of material mixing rates must be 100.')

        materials = [attr.get('material') for attr in attrs]
        if has_duplicate_element(materials):
            raise ValidationError('material is duplicated.')

        return attrs


class ProductMaterialSerializer(Serializer):
    id = IntegerField(required=False)
    product = PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, required=False)
    material = CharField(max_length=20)
    mixing_rate = IntegerField(max_value=100, min_value=1)

    class Meta:
        list_serializer_class = ProductMaterialListSerializer

    def validate(self, attrs):
        if self.root.partial:
            if not is_delete_data(attrs):
                validate_require_data_in_partial_update(attrs, self.fields)

        return attrs


class OptionListSerializer(ListSerializer):
    def validate(self, attrs):
        sizes = [attr.get('size') for attr in attrs]
        if has_duplicate_element(sizes):
            raise ValidationError("'size' is duplicated.")

        return attrs


class OptionSerializer(Serializer):
    id = IntegerField(required=False)
    size = CharField(max_length=20)
    price_difference = IntegerField(max_value=100000, min_value=0, required=False)

    class Meta:
        list_serializer_class = OptionListSerializer

    def validate(self, attrs):
        if self.root.partial and is_create_data(attrs):
            validate_require_data_in_partial_update(attrs, self.fields)
        elif self.root.partial and is_update_data(attrs):
            if 'size' in attrs:
                input_size = attrs.get('size')
                stored_size = Option.objects.get(id=attrs.get('id')).size

                if input_size != stored_size:
                    raise ValidationError('Size data cannot be updated.')

        return attrs


class ProductColorListSerializer(ListSerializer):
    def validate(self, attrs):
        if self.root.instance is not None:
            return self.validate_update(attrs)
        else:
            return self.validate_create(attrs)

    def validate_update(self, attrs):
        create_data = [attr for attr in attrs if is_create_data(attr)]
        delete_data = [attr for attr in attrs if is_delete_data(attr)]

        len_colors = self.root.instance.colors.all().count() + len(create_data) - len(delete_data)
        if len_colors > 10:
            raise ValidationError(
                'The product cannot have more than ten colors.'
            )

        display_color_name_attrs = [
            attr for attr in attrs if 'display_color_name' in attr
        ]

        if has_duplicate_element([attr.get('display_color_name') for attr in display_color_name_attrs]):
            raise ValidationError('display_color_name is duplicated.')

        self.validate_display_color_name_uniqueness(display_color_name_attrs)

        return attrs

    def validate_create(self, attrs):
        if len(attrs) > 10:
            raise ValidationError(
                'The product cannot have more than ten colors.'
            )

        display_color_names = [attr.get('display_color_name') for attr in attrs]
        if has_duplicate_element(display_color_names):
            raise ValidationError('display color name is duplicated.')

        image_urls = [attr.get('image_url') for attr in attrs]
        if has_duplicate_element(image_urls):
            raise ValidationError('image_url is duplicated.')

        return attrs

    def validate_display_color_name_uniqueness(self, attrs):
        for attr in attrs:
            queryset = ProductColor.objects.filter(
                on_sale=True, product=self.root.instance, 
                display_color_name=attr.get('display_color_name')
            )

            if is_update_data(attr):
                queryset = queryset.exclude(id=attr.get('id'))

            if queryset.exists():
                raise ValidationError(
                    'The product with the display_color_name already exists.'
                )

    def to_representation(self, data):
        iterable = data.filter(on_sale=True) if isinstance(data, Manager) else data

        return [
            self.child.to_representation(item) for item in iterable
        ]


class ProductColorSerializer(Serializer):
    id = IntegerField(required=False)
    display_color_name = CharField(allow_null=True, max_length=20)
    color = PrimaryKeyRelatedField(queryset=Color.objects.all())
    options = OptionSerializer(allow_empty=False, many=True)
    image_url = CharField(max_length=200)

    class Meta:
        list_serializer_class = ProductColorListSerializer

    def validate(self, attrs):
        if self.root.partial and is_update_data(attrs):
            product_color_id = attrs.get('id')
            if 'color' in attrs:
                input_color = attrs.get('color')
                stored_color = ProductColor.objects.get(id=product_color_id).color

                if input_color != stored_color:
                    raise ValidationError('Color data cannot be updated.')
            
            if 'options' in attrs:
                self.validate_option_size_uniqueness(attrs.get('options'), product_color_id)

        elif self.root.partial and is_create_data(attrs):
            validate_require_data_in_partial_update(attrs, self.fields)
        
        display_color_name = attrs.get('display_color_name', None)
        if display_color_name is None and not is_delete_data(attrs):
            attrs['display_color_name'] = attrs.get('color').name
        
        return attrs

    def validate_image_url(self, value):
        return validate_url(value)

    def validate_option_size_uniqueness(self, attrs, product_color_id):
        for attr in attrs:
            if 'size' in attr:
                queryset = Option.objects.filter(
                    product_color_id=product_color_id, size = attr.get('size')
                )

                if is_update_data(attr):
                    queryset = queryset.exclude(id=attr.get('id'))

                if queryset.exists():
                    raise ValidationError(
                        'The option with the size already exists.'
                    )
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class ProductSerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=60)
    price = IntegerField(max_value=1000000, min_value=0)
    lining = BooleanField()
    materials = ProductMaterialSerializer(allow_empty=False, many=True)
    colors = ProductColorSerializer(allow_empty=False, many=True)
    images = ProductImagesSerializer(allow_empty=False, many=True, source='related_images')
    
    def _sort_dictionary_by_field_name(self, ret_dict):
        for field in self.field_order:
            ret_dict.move_to_end(field, last=True)

        return ret_dict


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

    field_order = [
        'id', 'name', 'price', 'main_category', 'sub_category', 'style', 'age', 'tags', 
        'materials', 'laundry_informations', 'thickness', 'see_through', 'flexibility', 'lining', 'images', 'colors'
    ]

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
    sub_category = PrimaryKeyRelatedField( queryset=SubCategory.objects.all())
    style = PrimaryKeyRelatedField(queryset=Style.objects.all())
    age = PrimaryKeyRelatedField(queryset=Age.objects.all())
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    laundry_informations = PrimaryKeyRelatedField(allow_empty=False, many=True, queryset=LaundryInformation.objects.all())
    thickness = PrimaryKeyRelatedField(queryset=Thickness.objects.all())
    see_through = PrimaryKeyRelatedField( queryset=SeeThrough.objects.all())
    flexibility = PrimaryKeyRelatedField(queryset=Flexibility.objects.all())

    field_order = [
            'id', 'name', 'price', 'sub_category', 'style', 'age', 'tags', 
            'materials', 'laundry_informations', 'thickness', 'see_through', 'flexibility', 'lining', 'images', 'colors'
    ]

    def validate(self, attrs):
        if self.partial and 'price' not in attrs:
            price = getattr(self.instance, 'price', 0)
        else:
            price = attrs.get('price') 

        product_colors = attrs.get('colors', list())

        for product_color in product_colors:
            options_data = product_color.get('options', list())
            for option_data in options_data:
                validate_price_difference(price, option_data)

        return attrs


    def to_representation(self, instance):
        ret = super().to_representation(instance)
        self._sort_dictionary_by_field_name(ret)

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

            Option.objects.bulk_create(
                [Option(product_color=product_color, **option_data) for option_data in options]
            )

        ProductImages.objects.bulk_create(
            [ProductImages(product=product, **image_data) for image_data in images]
        )

        return product

    def update(self, instance, validated_data):
        laundry_informations_data = validated_data.pop('laundry_informations', list())
        tags_data = validated_data.pop('tags', None)
        materials_data = validated_data.pop('materials', None)
        product_colors_data = validated_data.pop('colors', None)
        product_images_data = validated_data.pop('related_images', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if tags_data is not None:
            self.update_id_only_m2m_fields(instance.tags, tags_data)

        if laundry_informations_data:
            self.update_id_only_m2m_fields(instance.laundry_informations, laundry_informations_data)

        if product_images_data is not None:
            self.update_images(instance, product_images_data)

        if materials_data is not None:
            self.update_materials(instance, materials_data)

        if product_colors_data is not None:
            self.update_product_colors(instance, product_colors_data)

        instance.save(update_fields=validated_data.keys())

        return instance

    def update_images(self, product, image_data):
        create_data, update_data, delete_data = self.get_separated_data_by_create_update_delete(image_data)
        self.update_many_to_one_fields(product, ProductImages, create_data, update_data, delete_data)

        if product.images.all().count()==0:
            raise APIException('The product must have at least one image.')

    def update_materials(self, product, material_data):
        create_data, update_data, delete_data = self.get_separated_data_by_create_update_delete(material_data)
        self.update_many_to_one_fields(product, ProductMaterial, create_data, update_data, delete_data)

    def update_product_colors(self, product, product_colors_data):
        create_data, update_data, delete_data = self.get_separated_data_by_create_update_delete(product_colors_data)

        delete_fields_id = [data['id'] for data in delete_data]
        ProductColor.objects.filter(product=product, id__in=delete_fields_id).update(on_sale=False, display_color_name=None)

        for data in update_data:
            options_data = data.pop('options', None)
            
            product_color_id = data.pop('id')
            ProductColor.objects.filter(id=product_color_id).update(**data)

            if options_data is not None:
                product_color = ProductColor.objects.get(id=product_color_id)
                self.update_options(product_color, options_data)

        for data in create_data:
            options_data = data.pop('options', None)

            product_color = ProductColor.objects.create(product=product, **data)
            Option.objects.bulk_create(
                [Option(product_color=product_color, **option_data) for option_data in options_data]
            )

        if product.colors.filter(on_sale=True).count()==0:
            raise APIException('The product must have at least one color.')

    def update_options(self, product_color, options_data):
        create_data, update_data, delete_data = self.get_separated_data_by_create_update_delete(options_data)
        
        delete_fields_id = [data['id'] for data in delete_data]
        Option.objects.filter(product_color=product_color, id__in=delete_fields_id).delete()

        for data in update_data:
            field_id = data.pop('id')
            Option.objects.filter(product_color=product_color, id=field_id).update(**data)

        Option.objects.bulk_create(
            [Option(product_color=product_color, **data) for data in create_data]
        )

    def update_many_to_one_fields(self, product, rel_model_class, create_data, update_data, delete_data):
        delete_fields_id = [data['id'] for data in delete_data]
        rel_model_class.objects.filter(product=product, id__in=delete_fields_id).delete()

        for data in update_data:
            field_id = data.pop('id')
            rel_model_class.objects.filter(product=product, id=field_id).update(**data)

        rel_model_class.objects.bulk_create(
            [rel_model_class(product=product, **data) for data in create_data]
        )

    def update_id_only_m2m_fields(self, m2m_field, validated_fields):
        model = m2m_field.model

        stored_fields = m2m_field.all()
        input_fields = model.objects.filter(id__in=[field.id for field in validated_fields])

        delete_fields = set(stored_fields) - set(input_fields)
        m2m_field.remove(*delete_fields)

        store_fields = set(input_fields) - set(stored_fields)
        m2m_field.add(*store_fields)

    def get_separated_data_by_create_update_delete(self, data_array):
        create_data = []
        delete_data = []
        update_data = []

        for data in data_array:
            if is_create_data(data):
                create_data.append(data)
            elif is_delete_data(data):
                delete_data.append(data)
            elif is_update_data:
                update_data.append(data)

        return (create_data, update_data, delete_data)


class MaterialSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(max_length=20, read_only=True)
