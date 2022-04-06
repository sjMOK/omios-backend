from rest_framework.serializers import (
    Serializer, ListSerializer, IntegerField, CharField, ImageField, DateTimeField,
    PrimaryKeyRelatedField, URLField, BooleanField, RegexField,
)
from rest_framework.exceptions import ValidationError, APIException

from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL 
from common.validators import validate_all_required_fields_included
from common.serializers import (
    has_duplicate_element ,is_create_data, is_update_data, is_delete_data, get_create_attrs,
    get_delete_attrs, get_create_or_update_attrs, get_update_or_delete_attrs, get_list_of_single_item,
    DynamicFieldsSerializer,
)
from .validators import validate_url
from .models import (
    LaundryInformation, SubCategory, Color, Option, Tag, Product, ProductImage, Style, Age, Thickness,
    SeeThrough, Flexibility, ProductMaterial, ProductColor, Theme,
)


PRODUCT_NAME_REGEX = r'^[\w\s!-~가-힣]+$'
PRODUCT_IMAGE_MAX_LENGTH = 10
PRODUCT_COLOR_MAX_LENGTH = 10


class SubCategorySerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class MainCategorySerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    image_url = ImageField(read_only=True)
    sub_categories = SubCategorySerializer(read_only=True, many=True)


class ColorSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    image_url = ImageField(read_only=True)


class SizeSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class LaundryInformationSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class ThicknessSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class SeeThroughSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class FlexibilitySerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class AgeSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class ThemeSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)  


class StyleSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class MaterialSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class TagSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class ProductImageListSerializer(ListSerializer):
    def validate(self, attrs):
        create_or_update_attrs = get_create_or_update_attrs(attrs)
        self.__validate_attrs_length(create_or_update_attrs)
        self.__validate_sequence_ascending_order(create_or_update_attrs)

        return attrs

    def __validate_attrs_length(self, attrs):
        if len(attrs) > PRODUCT_IMAGE_MAX_LENGTH:
            raise ValidationError(
                'The product cannot have more than ten images.'
            )
        elif len(attrs) == 0:
            raise ValidationError(
                'The product must have at least one image.'
            )

    def __validate_sequence_ascending_order(self, attrs):
        sequences = get_list_of_single_item('sequence', attrs)
        sequences.sort()

        for index, value in enumerate(sequences):
            if value != (index+1):
                raise ValidationError(
                    'The sequence of the images must be ascending from 1 to n.'
                )


class ProductImageSerializer(Serializer):
    id = IntegerField(required=False)
    image_url = URLField(max_length=200)
    sequence = IntegerField(min_value=1)

    class Meta:
        list_serializer_class = ProductImageListSerializer

    def validate(self, attrs):
        if self.root.partial and not is_delete_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)

        return attrs

    def validate_image_url(self, value):
        return validate_url(value)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class ProductMaterialListSerializer(ListSerializer):
    total_mixing_rates = 100

    def validate(self, attrs):
        create_or_update_attrs = get_create_or_update_attrs(attrs)
        self.__validate_materials(create_or_update_attrs)
        self.__validate_total_mixing_rates(create_or_update_attrs)

        return attrs

    def __validate_total_mixing_rates(self, attrs):
        total_mixing_rates = get_list_of_single_item('mixing_rate', attrs)

        if sum(total_mixing_rates) != self.total_mixing_rates:
            raise ValidationError('The total of material mixing rates must be 100.')

    def __validate_materials(self, attrs):
        materials = get_list_of_single_item('material', attrs)

        if has_duplicate_element(materials):
            raise ValidationError('Material is duplicated.')


class ProductMaterialSerializer(Serializer):
    id = IntegerField(required=False)
    material = CharField(max_length=20)
    mixing_rate = IntegerField(min_value=1, max_value=100)

    class Meta:
        list_serializer_class = ProductMaterialListSerializer

    def validate(self, attrs):
        if self.root.partial and not is_delete_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)

        return attrs


class OptionListSerializer(ListSerializer):
    def validate(self, attrs):
        if self.root.instance is None:
            return self.__validate_create(attrs)
        else:
            return self.__validate_update(attrs)

    def __validate_create(self, attrs):
        sizes = get_list_of_single_item('size', attrs)
        self.__validate_sizes(sizes)

        return attrs

    def __validate_update(self, attrs):
        create_or_update_attrs = get_create_or_update_attrs(attrs)
        sizes = [attr['size'] for attr in create_or_update_attrs if 'size' in attr]
        self.__validate_sizes(sizes)

        return attrs

    def __validate_sizes(self, attrs):
        if has_duplicate_element(attrs):
            raise ValidationError('size is duplicated.')


class OptionSerializer(Serializer):
    id = IntegerField(required=False)
    size = CharField(max_length=20)
    price_difference = IntegerField()
    on_sale = BooleanField(read_only=True)

    class Meta:
        list_serializer_class = OptionListSerializer

    def validate(self, attrs):
        if self.root.partial:
            self.__validate_partial_update(attrs)

        return attrs

    def __validate_partial_update(self, attrs):
        if is_create_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)
        elif is_update_data(attrs) and 'size' in attrs:
            self.__validate_size_update(attrs)

    def __validate_size_update(self, attrs):
        input_size = attrs.get('size', None)
        stored_size = Option.objects.get(id=attrs.get('id')).size

        if input_size != stored_size:
            raise ValidationError('Size data cannot be updated.')


class ProductColorListSerializer(ListSerializer):
    def validate(self, attrs):
        if self.root.instance is None:
            return self.__validate_create(attrs)
        else:
            return self.__validate_update(attrs)

    def __validate_create(self, attrs):
        if len(attrs) > PRODUCT_COLOR_MAX_LENGTH:
            raise ValidationError(
                'The product cannot have more than ten colors.'
            )

        display_color_names = get_list_of_single_item('display_color_name', attrs)
        if has_duplicate_element(display_color_names):
            raise ValidationError('display_color_name is duplicated.')

        return attrs

    def __validate_update(self, attrs):
        display_color_names = [attr.get('display_color_name') for attr in attrs if 'display_color_name' in attr]
        if has_duplicate_element(display_color_names):
            raise ValidationError('display_color_name is duplicated.')

        return attrs


class ProductColorSerializer(Serializer):
    id = IntegerField(required=False)
    display_color_name = CharField(max_length=20)
    color = PrimaryKeyRelatedField(queryset=Color.objects.all())
    options = OptionSerializer(allow_empty=False, many=True)
    image_url = URLField(max_length=200)
    on_sale = BooleanField(read_only=True)

    class Meta:
        list_serializer_class = ProductColorListSerializer

    def validate(self, attrs):
        if self.root.instance is not None:
            attrs = self.validate_update(attrs)

        return attrs

    def validate_update(self, attrs):
        if self.root.partial:
            return self.__validate_partial_update(attrs)

        return attrs

    def validate_image_url(self, value):
        return validate_url(value)

    def __validate_partial_update(self, attrs):
        if is_create_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)
        elif is_update_data(attrs):
            if 'color' in attrs:
                self.__validate_color_update(attrs)

            if 'options' in attrs:
                self.__validate_option_size_uniqueness(attrs)
                self.__validate_update_option_length(attrs)

        return attrs

    def __validate_color_update(self, attrs):
        input_color = attrs.get('color')
        stored_color = ProductColor.objects.get(id=attrs.get('id')).color

        if input_color != stored_color:
            raise ValidationError('Color data cannot be updated.')

    def __validate_option_size_uniqueness(self, attrs):
        option_attrs = attrs['options']

        delete_option_attrs_id_list = get_list_of_single_item(
            'id', get_delete_attrs(option_attrs)
        )
        create_option_attrs = get_create_attrs(option_attrs)
        for attr in create_option_attrs:
            queryset = Option.objects.filter(
                product_color_id=attrs['id'], size=attr['size']
            ).exclude(id__in=delete_option_attrs_id_list)

            if queryset.exists():
                raise ValidationError(
                    'The option with the size already exists.'
                )

    def __validate_update_option_length(self, attrs):
        color_id = attrs['id']

        if 'options' not in attrs:
            return

        create_option_len = len(get_create_attrs(attrs['options']))
        delete_option_len = len(get_delete_attrs(attrs['options']))
        
        product_color = ProductColor.objects.get(id=color_id)
        stored_option_length = product_color.options.filter(on_sale=True).count()

        if stored_option_length + create_option_len - delete_option_len <= 0:
            raise ValidationError('The product color must have at least one option.')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['image_url'] = BASE_IMAGE_URL + ret['image_url']

        return ret


class ProductSerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = RegexField(PRODUCT_NAME_REGEX, max_length=100)
    price = IntegerField(min_value=100, max_value=5000000)
    sale_price = IntegerField(read_only=True)
    base_discount_rate = IntegerField(read_only=True)
    base_discounted_price = IntegerField(read_only=True)
    lining = BooleanField()
    materials = ProductMaterialSerializer(allow_empty=False, many=True)
    colors = ProductColorSerializer(allow_empty=False, many=True)
    images = ProductImageSerializer(allow_empty=False, many=True, source='related_images')
    manufacturing_country = CharField(max_length=20)
    
    def __sort_dictionary_by_field_name(self, ret_dict):
        field_order = self.context.get('field_order', [])
        for field in field_order:
            if field in self.fields:
                ret_dict.move_to_end(field, last=True)

        return ret_dict

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret = self.__sort_dictionary_by_field_name(ret)

        return ret


class ProductReadSerializer(ProductSerializer):
    main_category = MainCategorySerializer(read_only=True, source='sub_category.main_category', exclude_fields=('sub_categories',))
    sub_category = SubCategorySerializer(read_only=True)
    style = StyleSerializer(read_only=True)
    age = AgeSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    laundry_informations = LaundryInformationSerializer(read_only=True, many=True)
    thickness = ThicknessSerializer(read_only=True)
    see_through = SeeThroughSerializer(read_only=True)
    flexibility = FlexibilitySerializer(read_only=True)
    theme = ThemeSerializer(read_only=True)
    created = DateTimeField(read_only=True)
    on_sale = BooleanField(read_only=True)
    code = CharField(read_only=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if self.context['detail']:
            ret = self.to_representation_retrieve(ret, instance)
        else:
            if instance.related_images:
                ret['main_image'] = BASE_IMAGE_URL + instance.related_images[0].image_url
            else:
                ret['main_image'] = DEFAULT_IMAGE_URL

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
    laundry_informations = PrimaryKeyRelatedField(many=True, queryset=LaundryInformation.objects.all())
    thickness = PrimaryKeyRelatedField(queryset=Thickness.objects.all())
    see_through = PrimaryKeyRelatedField( queryset=SeeThrough.objects.all())
    flexibility = PrimaryKeyRelatedField(queryset=Flexibility.objects.all())
    theme = PrimaryKeyRelatedField(required=False, default=Theme.objects.get(id=1), queryset=Theme.objects.all())

    color_length_limit = 10
    price_difference_upper_limit_ratio = 0.2

    def validate(self, attrs):
        if self.partial and 'price' not in attrs:
            price = getattr(self.instance, 'price', 0)
        else:
            price = attrs.get('price') 

        product_colors = attrs.get('colors', [])

        for product_color in product_colors:
            options_data = product_color.get('options', [])
            for option_data in options_data:
                if 'price_difference' in option_data:
                    self.__validate_price_difference(price, option_data)

        return attrs

    def validate_images(self, attrs):
        if self.instance is not None:
            update_or_delete_attrs = get_update_or_delete_attrs(attrs)
            self.__validate_pass_all_exact_data(update_or_delete_attrs, self.instance.images)

        return attrs

    def validate_materials(self, attrs):
        if self.instance is not None:
            update_or_delete_attrs = get_update_or_delete_attrs(attrs)
            self.__validate_pass_all_exact_data(update_or_delete_attrs, self.instance.materials)

        return attrs

    def validate_colors(self, attrs):
        if self.instance is not None:
            self.__validate_color_length(attrs)
            self.__validate_display_color_name_uniqueness(attrs)

        return attrs

    def __validate_color_length(self, attrs):
        create_color_length = len(get_create_attrs(attrs))
        delete_color_length = len(get_delete_attrs(attrs))

        stored_color_length = self.instance.colors.filter(on_sale=True).count()
        len_colors = stored_color_length + create_color_length - delete_color_length

        if len_colors > PRODUCT_COLOR_MAX_LENGTH:
            raise ValidationError(
                'The product cannot have more than ten colors.'
            )
        elif len_colors == 0:
            raise ValidationError(
                'The product must have at least one color.'
            )

    def __validate_display_color_name_uniqueness(self, attrs):
        delete_attrs_id_list = get_list_of_single_item(
            'id', get_delete_attrs(attrs)
        )
        display_color_name_attrs = [
            attr for attr in attrs if 'display_color_name' in attr
        ]

        for attr in display_color_name_attrs:
            queryset = ProductColor.objects.filter(
                on_sale=True, product=self.instance,
                display_color_name=attr.get('display_color_name')
            ).exclude(id__in=delete_attrs_id_list)

            if is_update_data(attr):
                queryset = queryset.exclude(id=attr.get('id'))

            if queryset.exists():
                raise ValidationError(
                    'The product with the display_color_name already exists.'
                )
    
    def __validate_pass_all_exact_data(self, attrs, related_manager):
        id_list = get_list_of_single_item('id', attrs)

        if related_manager.exclude(id__in=id_list):
            raise ValidationError(
                'You must contain all exact data that the product has.'
            )

    def __validate_price_difference(self, price, option_data):
        price_difference = option_data.get('price_difference', 0)
        price_difference = option_data['price_difference']
        
        if abs(price_difference) > price * self.price_difference_upper_limit_ratio:
            raise ValidationError(
                'The option price difference must be less than {0}% of the product price.'
                .format(self.price_difference_upper_limit_ratio * 100)
            )
    
    def create(self, validated_data):
        laundry_informations = validated_data.pop('laundry_informations', [])
        tags = validated_data.pop('tags', [])
        materials = validated_data.pop('materials')
        colors = validated_data.pop('colors')
        images = validated_data.pop('related_images')

        product = Product.objects.create(wholesaler=self.context['wholesaler'], **validated_data)
        product.laundry_informations.add(*laundry_informations)
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

        ProductImage.objects.bulk_create(
            [ProductImage(product=product, **image_data) for image_data in images]
        )

        return product

    def update(self, instance, validated_data):
        laundry_informations_data = validated_data.pop('laundry_informations', None)
        tags_data = validated_data.pop('tags', None)
        materials_data = validated_data.pop('materials', None)
        product_colors_data = validated_data.pop('colors', None)
        product_images_data = validated_data.pop('related_images', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if tags_data is not None:
            self.__update_id_only_m2m_fields(instance.tags, tags_data)

        if laundry_informations_data is not None:
            self.__update_id_only_m2m_fields(instance.laundry_informations, laundry_informations_data)

        if product_images_data is not None:
            self.__update_many_to_one_fields(instance, ProductImage, product_images_data)

        if materials_data is not None:
            self.__update_many_to_one_fields(instance, ProductMaterial, materials_data)

        if product_colors_data is not None:
            self.__update_product_colors(instance, product_colors_data)

        instance.save(update_fields=validated_data.keys())

        return instance

    def __update_product_colors(self, product, product_colors_data):
        create_data, update_data, delete_data = self.__get_separated_data_by_create_update_delete(product_colors_data)

        delete_fields_id = [data['id'] for data in delete_data]
        ProductColor.objects.filter(product=product, id__in=delete_fields_id).update(on_sale=False, display_color_name=None)
        Option.objects.filter(product_color__product=product, product_color_id__in=delete_fields_id).update(on_sale=False)

        for data in update_data:
            options_data = data.pop('options', None)
            
            product_color_id = data.pop('id')
            ProductColor.objects.filter(id=product_color_id).update(**data)

            if options_data is not None:
                product_color = ProductColor.objects.get(id=product_color_id)
                self.__update_options(product_color, options_data)

        for data in create_data:
            options_data = data.pop('options', None)

            product_color = ProductColor.objects.create(product=product, **data)
            Option.objects.bulk_create(
                [Option(product_color=product_color, **option_data) for option_data in options_data]
            )

    def __update_options(self, product_color, options_data):
        create_data, update_data, delete_data = self.__get_separated_data_by_create_update_delete(options_data)
        
        delete_fields_id = [data['id'] for data in delete_data]
        Option.objects.filter(product_color=product_color, id__in=delete_fields_id).update(on_sale=False)

        for data in update_data:
            field_id = data.pop('id')
            Option.objects.filter(product_color=product_color, id=field_id).update(**data)

        Option.objects.bulk_create(
            [Option(product_color=product_color, **data) for data in create_data]
        )

    def __update_many_to_one_fields(self, product, rel_model_class, data):
        create_data, update_data, delete_data = self.__get_separated_data_by_create_update_delete(data)

        delete_fields_id = [data['id'] for data in delete_data]
        rel_model_class.objects.filter(product=product, id__in=delete_fields_id).delete()

        for data in update_data:
            field_id = data.pop('id')
            rel_model_class.objects.filter(product=product, id=field_id).update(**data)

        rel_model_class.objects.bulk_create(
            [rel_model_class(product=product, **data) for data in create_data]
        )

    def __update_id_only_m2m_fields(self, m2m_field, validated_fields):
        model = m2m_field.model

        stored_fields = m2m_field.all()
        input_fields = model.objects.filter(id__in=[field.id for field in validated_fields])

        delete_fields = set(stored_fields) - set(input_fields)
        m2m_field.remove(*delete_fields)

        store_fields = set(input_fields) - set(stored_fields)
        m2m_field.add(*store_fields)

    def __get_separated_data_by_create_update_delete(self, data_array):
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
