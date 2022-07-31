from django.core.validators import URLValidator
from django.db.models import Sum

from rest_framework.serializers import (
    Serializer, ListSerializer, ModelSerializer, IntegerField, CharField, ImageField, DateTimeField,
    PrimaryKeyRelatedField, BooleanField, RegexField,
)
from rest_framework.exceptions import ValidationError, APIException

from common.utils import DEFAULT_IMAGE_URL, BASE_IMAGE_URL
from common.regular_expressions import BASIC_SPECIAL_CHARACTER_REGEX, ENG_OR_KOR_REGEX, SIZE_REGEX, IMAGE_URL_REGEX
from common.validators import validate_all_required_fields_included, validate_image_url
from common.serializers import (
    has_duplicate_element ,is_create_data, is_update_data, is_delete_data, get_create_attrs, get_update_attrs,
    get_delete_attrs, get_create_or_update_attrs, get_update_or_delete_attrs, get_list_of_single_value,
    get_separated_data_by_create_update_delete,
    DynamicFieldsSerializer, DynamicFieldsModelSerializer,
)
from .models import (
    Size, LaundryInformation, SubCategory, MainCategory, Color, Option, Tag, Product, ProductImage, Style, Age, Thickness,
    SeeThrough, Flexibility, ProductMaterial, ProductColor, ProductQuestionAnswer, Material,
)


PRODUCT_IMAGE_MAX_LENGTH = 10
PRODUCT_COLOR_MAX_LENGTH = 10


class SubCategorySerializer(ModelSerializer):
    class Meta:
        model = SubCategory
        exclude = ['main_category', 'sizes', 'require_product_additional_information', 'require_laundry_information']
        extra_kwargs = {
            'name': {'read_only': True},
        }


class MainCategorySerializer(DynamicFieldsModelSerializer):
    sub_categories = SubCategorySerializer(read_only=True, many=True)
    class Meta:
        model = MainCategory
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
            'image_url': {'read_only': True},
        }


class ColorSerializer(ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
            'image_url': {'read_only': True}
        }


class SizeSerializer(ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }

class LaundryInformationSerializer(ModelSerializer):
    class Meta:
        model = LaundryInformation
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class ThicknessSerializer(ModelSerializer):
    class Meta:
        model = Thickness
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class SeeThroughSerializer(ModelSerializer):
    class Meta:
        model = SeeThrough
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class FlexibilitySerializer(ModelSerializer):
    class Meta:
        model = Flexibility
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class AgeSerializer(ModelSerializer):
    class Meta:
        model = Age
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class StyleSerializer(ModelSerializer):
    class Meta:
        model = Style
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class MaterialSerializer(ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        extra_kwargs = {
            'name': {'read_only': True},
        }


class ProductImageListSerializer(ListSerializer):
    def create(self, validated_data, product):
        images = [self.child.Meta.model(product=product, **data) for data in validated_data]
        self.child.Meta.model.objects.bulk_create(images)

    def update(self, validated_data, product):
        create_data, update_data, delete_data = get_separated_data_by_create_update_delete(validated_data)

        delete_id_list = [data['id'] for data in delete_data]
        product.images.filter(id__in=delete_id_list).delete()

        for data in update_data:
            product.images.filter(id=data['id']).update(**data)

        self.create(create_data, product)

    def validate(self, attrs):
        if self.root.instance is None:
            return self.__validate_create(attrs)
        else:
            return self.__validate_update(attrs)

    def __validate_create(self, attrs):
        self.__validate_image_number_in_create(attrs)
        self.__validate_sequence_in_create(attrs)

        return attrs

    def __validate_update(self, attrs):
        self.__validate_image_number_in_update(attrs)
        self.__validate_sequence_in_update(attrs)

        return attrs

    def __validate_image_number_in_create(self, attrs):
        if len(attrs) > PRODUCT_IMAGE_MAX_LENGTH:
            raise ValidationError(
                'The product cannot have more than ten images.'
            )

    def __validate_image_number_in_update(self, attrs):
        stored_image_length = self.root.instance.images.all().count()
        image_length = stored_image_length + len(get_create_attrs(attrs)) - len(get_delete_attrs(attrs))

        if image_length > PRODUCT_IMAGE_MAX_LENGTH:
            raise ValidationError(
                'The product cannot have more than ten images.'
            )
        elif image_length == 0:
            raise ValidationError(
                'The product must have at least one image.'
            )

    def ___validate_sequence(self, sequences):
        for index, value in enumerate(sequences):
            if value != (index+1):
                raise ValidationError(
                    'The sequence of the images must be ascending from 1 to n.'
                )

    def __validate_sequence_in_create(self, attrs):
        sequences = get_list_of_single_value(attrs, 'sequence')
        sequences.sort()

        self.___validate_sequence(sequences)

    def __validate_sequence_in_update(self, attrs):
        sequences = get_list_of_single_value(
            get_create_or_update_attrs(attrs), 'sequence'
        )
        exclude_id_list = get_list_of_single_value(
            get_update_or_delete_attrs(attrs), 'id'
        )
        stored_sequences = ProductImage.objects.filter(
            product=self.root.instance
        ).exclude(id__in=exclude_id_list).values_list('sequence', flat=True)

        sequences += stored_sequences
        sequences.sort()

        self.___validate_sequence(sequences)


class ProductImageSerializer(ModelSerializer):
    id = IntegerField(required=False)
    image_url = RegexField(IMAGE_URL_REGEX, max_length=200, validators=[URLValidator])
    sequence = IntegerField(min_value=1)

    class Meta:
        model = ProductImage
        exclude = ['product']
        list_serializer_class = ProductImageListSerializer

    def validate_image_url(self, value):
        return value.split(BASE_IMAGE_URL)[-1]

    def validate(self, attrs):
        if self.root.instance is None:
            return self.__validate_create(attrs)
        else:
            return self.__validate_update(attrs)

    def __validate_create(self, attrs):
        validate_image_url(attrs['image_url'])

        return attrs

    def __validate_update(self, attrs):
        if is_create_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)
            validate_image_url(attrs['image_url'])
        elif is_update_data(attrs):
            if 'image_url' in attrs:
                self.__validate_image_url_update(attrs)

        return attrs

    def __validate_image_url_update(self, attrs):
        stored_image_url = ProductImage.objects.get(id=attrs.get('id')).image_url
        if attrs['image_url'] != stored_image_url:
            raise ValidationError('Image url data cannot be updated.')

    def to_representation(self, instance):
        result = super().to_representation(instance)

        result['image_url'] = BASE_IMAGE_URL + result['image_url']

        return result


class ProductMaterialListSerializer(ListSerializer):
    __total_mixing_rates = 100

    def create(self, validated_data, product):
        materials = [self.child.Meta.model(product=product, **data) for data in validated_data]
        self.child.Meta.model.objects.bulk_create(materials)

    def update(self, validated_data, product):
        create_data, update_data, delete_data = get_separated_data_by_create_update_delete(validated_data)

        delete_id_list = [data['id'] for data in delete_data]
        product.materials.filter(id__in=delete_id_list).delete()

        for data in update_data:
            product.materials.filter(id=data['id']).update(**data)

        self.create(create_data, product)
    
    def validate(self, attrs):
        if self.root.instance is None:
            return self.__validate_create(attrs)
        else:
            return self.__validate_update(attrs)

    def __validate_create(self, attrs):
        self.__validate_material_is_duplicated(attrs)
        self.__validate_total_mixing_rates_in_create(attrs)

        return attrs

    def __validate_update(self, attrs):
        self.__validate_material_is_duplicated(attrs)
        self.__validate_total_mixing_rates_in_update(attrs)
        self.__validate_material_name_uniqueness(attrs)

        return attrs

    def __validate_total_mixing_rates_in_create(self, attrs):
        total_mixing_rates = get_list_of_single_value(attrs, 'mixing_rate')

        if sum(total_mixing_rates) != self.__total_mixing_rates:
            raise ValidationError('The total of material mixing rates must be 100.')

    def __validate_total_mixing_rates_in_update(self, attrs):
        deleting_id_list = get_list_of_single_value(
            get_delete_attrs(attrs), 'id'
        )
        updating_mixing_rate_id_list = [attr['id'] for attr in get_update_attrs(attrs) if 'mixing_rate' in attr]
        exclude_id_list = deleting_id_list + updating_mixing_rate_id_list

        sum_of_mixing_rates = self.root.instance.materials.exclude(
            id__in=exclude_id_list
        ).aggregate(sum=Sum('mixing_rate', default=0))['sum']
        sum_of_mixing_rates += sum(get_list_of_single_value(attrs, 'mixing_rate'))

        if sum_of_mixing_rates != self.__total_mixing_rates:
            raise ValidationError('The total of material mixing rates must be 100.')

    def __validate_material_name_uniqueness(self, attrs):
        deleting_id_list = get_list_of_single_value(
            get_delete_attrs(attrs), 'id'
        )
        updating_material_attrs = [
            attr for attr in attrs if 'material' in attr
        ]
        updating_material_names = get_list_of_single_value(updating_material_attrs, 'material')
        updating_material_id_list = get_list_of_single_value(updating_material_attrs, 'id')

        exclude_id_list = deleting_id_list + updating_material_id_list

        if self.root.instance.materials.exclude(id__in=exclude_id_list).filter(material__in=updating_material_names).exists():
            raise ValidationError('The product with the material already exists.')

    def __validate_material_is_duplicated(self, attrs):
        materials = get_list_of_single_value(attrs, 'material')

        if has_duplicate_element(materials):
            raise ValidationError('Material is duplicated.')


class ProductMaterialSerializer(ModelSerializer):
    id = IntegerField(required=False)
    material = RegexField(ENG_OR_KOR_REGEX, max_length=20)
    mixing_rate = IntegerField(min_value=1, max_value=100)

    class Meta:
        model = ProductMaterial
        exclude = ['product']
        list_serializer_class = ProductMaterialListSerializer

    def validate(self, attrs):
        if self.root.instance is not None:
            self.__validate_update(attrs)

        return attrs

    def __validate_update(self, attrs):
        if is_create_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)


class OptionListSerializer(ListSerializer):
    def validate(self, attrs):
        self.__validate_size_is_duplicated(attrs)

        return attrs

    def __validate_size_is_duplicated(self, attrs):
        sizes = get_list_of_single_value(attrs, 'size')

        if has_duplicate_element(sizes):
            raise ValidationError('Size is duplicated.')

    def create(self, validated_data, product_color):
        options = [self.child.Meta.model(product_color=product_color, **data) for data in validated_data]
        self.child.Meta.model.objects.bulk_create(options)

    def update(self, validated_data, product_color):
        create_data, update_data, delete_data = get_separated_data_by_create_update_delete(validated_data)

        delete_id_list = [data['id'] for data in delete_data]
        product_color.options.filter(id__in=delete_id_list).update(on_sale=False)

        for data in update_data:
            product_color.options.filter(id=data['id']).update(**data)

        self.create(create_data, product_color)


class OptionSerializer(ModelSerializer):
    id = IntegerField(required=False)
    size = RegexField(SIZE_REGEX, max_length=20)

    class Meta:
        model = Option
        exclude = ['product_color']
        extra_kwargs = {
            'on_sale': {'read_only': True},
        }
        list_serializer_class = OptionListSerializer

    def validate(self, attrs):
        if self.root.instance is not None:
            self.__validate_update(attrs)

        return attrs

    def __validate_update(self, attrs):
        if is_create_data(attrs):
            validate_all_required_fields_included(attrs, self.fields)
        elif is_update_data(attrs):
            if 'size' in attrs:
                self.__validate_size_update(attrs)

    def __validate_size_update(self, attrs):
        stored_size = Option.objects.get(id=attrs.get('id')).size
        if attrs['size'] != stored_size:
            raise ValidationError('Size data cannot be updated.')


class OptionInOrderItemSerializer(Serializer):
    id = IntegerField(read_only=True)
    size = CharField(read_only=True)
    display_color_name = CharField(read_only=True, source='product_color.display_color_name')
    product_id = IntegerField(read_only=True, source='product_color.product.id')
    product_name = CharField(read_only=True, source='product_color.product.name')
    product_code = CharField(read_only=True, source='product_color.product.code')

    def to_representation(self, instance):
        result = super().to_representation(instance)

        if instance.product_color.product.images.all().exists():
            result['product_image_url'] = BASE_IMAGE_URL + instance.product_color.product.images.all()[0].image_url
        else:
            result['product_image_url'] = DEFAULT_IMAGE_URL

        return result


class ProductColorListSerializer(ListSerializer):
    def validate(self, attrs):
        if self.root.instance is None:
            return self.__validate_create(attrs)
        else:
            return self.__validate_update(attrs)

    def __validate_create(self, attrs):
        self.__validate_color_length_in_create(attrs)
        self.__validate_display_color_name_is_duplicated(attrs)

        return attrs

    def __validate_update(self, attrs):
        self.__validate_color_length_in_update(attrs)
        self.__validate_display_color_name_is_duplicated(attrs)
        self.__validate_display_color_name_uniqueness(attrs)

        return attrs

    def __validate_color_length_in_create(self, attrs):
        if len(attrs) > PRODUCT_COLOR_MAX_LENGTH:
            raise ValidationError(
                'The product cannot have more than ten colors.'
            )

    def __validate_color_length_in_update(self, attrs):
        create_color_length = len(get_create_attrs(attrs))
        delete_color_length = len(get_delete_attrs(attrs))

        stored_color_length = self.root.instance.colors.filter(on_sale=True).count()
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
        deleting_id_list = get_list_of_single_value(
            get_delete_attrs(attrs), 'id'
        )
        updating_display_color_name_attrs = [
            attr for attr in attrs if 'display_color_name' in attr
        ]
        updating_display_color_names = get_list_of_single_value(updating_display_color_name_attrs, 'display_color_name')
        updating_display_color_name_id_list = get_list_of_single_value(updating_display_color_name_attrs, 'id')
        
        exclude_id_list = deleting_id_list + updating_display_color_name_id_list

        if self.root.instance.colors.exclude(id__in=exclude_id_list).filter(display_color_name__in=updating_display_color_names, on_sale=True).exists():
            raise ValidationError(
                'The product with the display_color_name already exists.'
            )

    def __validate_display_color_name_is_duplicated(self, attrs):
        display_color_names = get_list_of_single_value(attrs, 'display_color_name')
        if has_duplicate_element(display_color_names):
            raise ValidationError('display_color_name is duplicated.')

    def create(self, validated_data, product):
        for data in validated_data:
            options = data.pop('options')
            product_color = self.child.Meta.model.objects.create(product=product, **data)
            self.child.fields['options'].create(options, product_color)

    def update(self, validated_data, product):
        create_data, update_data, delete_data = get_separated_data_by_create_update_delete(validated_data)

        delete_id_list = [data['id'] for data in delete_data]
        product.colors.filter(id__in=delete_id_list).delete()

        for data in update_data:
            options = data.pop('options', None)
            product.colors.filter(id=data['id']).update(**data)

            if options is not None:
                product_color = ProductColor.objects.get(id=data['id'])
                self.child.fields['options'].update(options, product_color)

        for data in create_data:
            options = data.pop('options', None)
            product_color = self.child.Meta.model.objects.create(product=product, **data)

            if options is not None:
                self.child.fields['options'].create(options, product_color)

class ProductColorSerializer(ModelSerializer):
    id = IntegerField(required=False)
    options = OptionSerializer(allow_empty=False, many=True)
    image_url = RegexField(IMAGE_URL_REGEX, max_length=200, validators=[URLValidator])

    class Meta:
        model = ProductColor
        exclude = ['product']
        extra_kwargs = {
            'on_sale': {'read_only': True},
        }
        list_serializer_class = ProductColorListSerializer

    def validate(self, attrs):
        if self.root.instance is not None:
            attrs = self.__validate_update(attrs)

        return attrs

    def validate_image_url(self, value):
        image_url = value.split(BASE_IMAGE_URL)[-1]
        return validate_image_url(image_url)

    def __validate_update(self, attrs):
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
        stored_color = ProductColor.objects.get(id=attrs.get('id')).color

        if attrs['color'] != stored_color:
            raise ValidationError('Color data cannot be updated.')

    def __validate_option_size_uniqueness(self, attrs):
        option_attrs = attrs['options']
        
        delete_option_attrs_id_list = get_list_of_single_value(
            get_delete_attrs(option_attrs), 'id'
        )
        create_option_attrs = get_create_attrs(option_attrs)
        for create_option_attr in create_option_attrs:
            queryset = Option.objects.filter(
                product_color_id=attrs['id'], size=create_option_attr['size']
            ).exclude(id__in=delete_option_attrs_id_list)

            if queryset.exists():
                raise ValidationError(
                    'The option with the size already exists.'
                )

    def __validate_update_option_length(self, attrs):
        color_id = attrs['id']

        create_option_len = len(get_create_attrs(attrs['options']))
        delete_option_len = len(get_delete_attrs(attrs['options']))
        
        product_color = ProductColor.objects.get(id=color_id)
        stored_option_length = product_color.options.filter(on_sale=True).count()

        if stored_option_length + create_option_len - delete_option_len <= 0:
            raise ValidationError('The product color must have at least one option.')

    def to_representation(self, instance):
        result = super().to_representation(instance)
        
        result['image_url'] = BASE_IMAGE_URL + result['image_url']

        return result



class ProductModelSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductSerializer(DynamicFieldsSerializer):
    id = IntegerField(read_only=True)
    name = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=100)
    price = IntegerField(min_value=100, max_value=5000000)
    sale_price = IntegerField(read_only=True)
    base_discount_rate = IntegerField(default=0)
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
        result = super().to_representation(instance)
        result = self.__sort_dictionary_by_field_name(result)

        return result


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
    created_at = DateTimeField(read_only=True)
    on_sale = BooleanField(read_only=True)
    code = CharField(read_only=True)
    total_like = IntegerField(read_only=True)

    def to_representation(self, instance):
        result = super().to_representation(instance)

        if self.context['detail']:
            return self.__to_representation_retrieve(result, instance)
        else:
            return self.__to_representation_list(result, instance)

    def __to_representation_list(self, result, instance):
        if instance.related_images:
            result['main_image'] = BASE_IMAGE_URL + instance.related_images[0].image_url
        else:
            result['main_image'] = DEFAULT_IMAGE_URL

        if result['id'] in self.context.get('shoppers_like_products_id_list', []):
            result['shopper_like'] = True
        else:
            result['shopper_like'] = False

        return result

    def __to_representation_retrieve(self, result, instance):
        if not instance.related_images:
            result['images'] = [DEFAULT_IMAGE_URL]

        result['shopper_like'] = self.context.get('shopper_like', False)

        return result


class ProductWriteSerializer(ProductSerializer):
    sub_category = PrimaryKeyRelatedField( queryset=SubCategory.objects.all())
    style = PrimaryKeyRelatedField(queryset=Style.objects.all())
    age = PrimaryKeyRelatedField(queryset=Age.objects.all())
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)
    laundry_informations = PrimaryKeyRelatedField(many=True, queryset=LaundryInformation.objects.all(), allow_empty=False)
    thickness = PrimaryKeyRelatedField(queryset=Thickness.objects.all())
    see_through = PrimaryKeyRelatedField( queryset=SeeThrough.objects.all())
    flexibility = PrimaryKeyRelatedField(queryset=Flexibility.objects.all())

    __price_multiple_num_data = [
        {'min_price': 0, 'multiple': 2.3},
        {'min_price': 40000, 'multiple': 2},
        {'min_price': 80000, 'multiple': 1.8},
    ]

    def validate_price(self, value):
        if value % 100 != 0:
            raise ValidationError('The price must be a multiple of 100.')

        return value

    def validate(self, attrs):
        if self.instance is not None and not self.partial:
            raise APIException('This serializer must have a partial=True parameter when update')

        return attrs

    def __get_price_multiple(self, price):
        index = 0
        for i in range(len(self.__price_multiple_num_data)):
            if price < self.__price_multiple_num_data[i]['min_price']:
                break
            index = i

        return self.__price_multiple_num_data[index]['multiple']

    def __get_sale_price(self, price):
        return round(price * self.__get_price_multiple(price)) // 100 * 100

    def __get_base_discounted_price(self, sale_price, base_discount_rate):
        base_discount_price = int(sale_price * base_discount_rate / 100) // 100 * 100
        return sale_price - base_discount_price

    def __update_price_data(self, instance, validated_data):
        if 'price' in validated_data:
            sale_price = self.__get_sale_price(validated_data['price'])
            validated_data['sale_price'] = sale_price
            base_discounted_price = self.__get_base_discounted_price(
                sale_price, instance.base_discount_rate
            )
            validated_data['base_discounted_price'] = base_discounted_price
        else:
            sale_price = instance.sale_price

        if 'base_discount_rate' in validated_data:
            base_discounted_price = self.__get_base_discounted_price(
                sale_price, validated_data['base_discount_rate']
            )
            validated_data['base_discounted_price'] = base_discounted_price

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        laundry_informations = validated_data.pop('laundry_informations', [])
        images = validated_data.pop('related_images')
        materials = validated_data.pop('materials')
        colors = validated_data.pop('colors')

        sale_price = self.__get_sale_price(validated_data['price'])
        base_discounted_price = self.__get_base_discounted_price(sale_price, validated_data['base_discount_rate'])

        product = Product.objects.create(
            sale_price=sale_price, base_discounted_price=base_discounted_price, 
            wholesaler=self.context['wholesaler'], **validated_data
        )

        product.tags.add(*tags)
        product.laundry_informations.add(*laundry_informations)
        self.fields['images'].create(images, product)
        self.fields['materials'].create(materials, product)
        self.fields['colors'].create(colors, product)

        return product

    def update(self, instance, validated_data):
        laundry_informations_data = validated_data.pop('laundry_informations', None)
        tags_data = validated_data.pop('tags', None)
        materials = validated_data.pop('materials', None)
        colors = validated_data.pop('colors', None)
        images = validated_data.pop('related_images', None)

        self.__update_price_data(instance, validated_data)            

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if tags_data is not None:
            self.__update_id_only_m2m_fields(instance.tags, tags_data)

        if laundry_informations_data is not None:
            self.__update_id_only_m2m_fields(instance.laundry_informations, laundry_informations_data)

        if images is not None:
            self.fields['images'].update(images, instance)

        if materials is not None:
            self.fields['materials'].update(materials, instance)

        if colors is not None:
            self.fields['colors'].update(colors, instance)

        instance.save(update_fields=validated_data.keys())

        return instance

    def __update_id_only_m2m_fields(self, m2m_field, validated_fields):
        model = m2m_field.model

        stored_fields = m2m_field.all()
        input_fields = model.objects.filter(id__in=[field.id for field in validated_fields])

        delete_fields = set(stored_fields) - set(input_fields)
        m2m_field.remove(*delete_fields)

        store_fields = set(input_fields) - set(stored_fields)
        m2m_field.add(*store_fields)


class ProductQuestionAnswerClassificationSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


class ProductQuestionAnswerSerializer(ModelSerializer):
    class Meta:
        model = ProductQuestionAnswer
        exclude = ['product']
        extra_kwargs = {
            'shopper': {'read_only': True},
            'answer': {'read_only': True},
            'classification': {'write_only': True},
        }

    def __get_username(self, username):
        return username[:3] + '***'

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result['classification'] = instance.classification.name
        result['username'] = self.__get_username(instance.shopper.username)

        return result
