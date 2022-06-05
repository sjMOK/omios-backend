from django.utils import timezone

from rest_framework.serializers import (
    Serializer, ModelSerializer, ListSerializer, ValidationError, IntegerField, CharField, RegexField, DateTimeField,
    StringRelatedField,
)
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, TokenBlacklistSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch

from order.serializers import ORDER_MAXIMUM_NUMBER
from common.utils import gmt_to_kst, BASE_IMAGE_URL, DEFAULT_IMAGE_URL
from common.regular_expressions import (
    USERNAME_REGEX, PASSWORD_REGEX, NAME_REGEX, NICKNAME_REGEX, MOBILE_NUMBER_REGEX, PHONE_NUMBER_REGEX,
    BASIC_SPECIAL_CHARACTER_REGEX, ZIP_CODE_REGEX,
)
from .models import (
    is_shopper, is_wholesaler, OutstandingToken, BlacklistedToken, ShopperShippingAddress, Membership, User, Shopper,
    Wholesaler, PointHistory, Building, Cart,
)
from .validators import PasswordSimilarityValidator


def get_token_time(token):
    return {
        'created_at': gmt_to_kst(token.current_time),
        'expires_at': gmt_to_kst(datetime_from_epoch(token['exp']))
    }


class IssuingTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        if is_shopper(user):
            token['user_type'] = 'shopper'
        elif is_wholesaler(user):
            token['user_type'] = 'wholesaler'

        OutstandingToken.objects.filter(jti=token['jti']).update(
            token=token,
            **get_token_time(token),
        )
        
        return token


class RefreshingTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = super().validate(attrs)
        refresh = RefreshToken(token['refresh'])
    
        OutstandingToken.objects.create(
            user=User.objects.get(id=refresh['user_id']),
            jti=refresh['jti'],
            token=str(refresh),
            **get_token_time(refresh),
        )
        
        return token


class MembershipSerializer(ModelSerializer):
    class Meta:
        model = Membership
        exclude = ['qualification']


class UserSerializer(ModelSerializer):
    username = RegexField(USERNAME_REGEX, min_length=4, max_length=20, validators=[UniqueValidator(queryset=User.objects.all())])
    password = RegexField(PASSWORD_REGEX, max_length=128, min_length=10, write_only=True)
    last_update_password = DateTimeField(required=False)

    class Meta:
        model = User
        fields = '__all__'

    def validate(self, attrs):
        if 'password' in attrs.keys():
            PasswordSimilarityValidator().validate(attrs['password'], attrs['username'])

        return attrs

    def update(self, instance, validated_data):
        for key, value in validated_data.items():            
            setattr(instance, key, value)
        
        instance.save(update_fields=validated_data.keys())
        
        return instance


class ShopperSerializer(UserSerializer):
    membership = MembershipSerializer(required=False)
    name = RegexField(NAME_REGEX, max_length=20)
    nickname = RegexField(NICKNAME_REGEX, min_length=4, max_length=20, required=False, validators=[UniqueValidator(queryset=Shopper.objects.all())])
    mobile_number = RegexField(MOBILE_NUMBER_REGEX, validators=[UniqueValidator(queryset=Shopper.objects.all())])
    point = IntegerField(read_only=True)

    class Meta:
        model = Shopper
        exclude = ['like_products']
        extra_kwargs = {            
            'height': {'min_value': 100, 'max_value': 250},
            'weight': {'min_value': 30, 'max_value': 200},
        }


class WholesalerSerializer(UserSerializer):
    mobile_number = RegexField(MOBILE_NUMBER_REGEX)
    phone_number = RegexField(PHONE_NUMBER_REGEX)
    company_registration_number = CharField(max_length=12, validators=[UniqueValidator(queryset=Wholesaler.objects.all())])
    business_registration_image_url = CharField(max_length=200)

    class Meta:
        model = Wholesaler
        fields = '__all__'


class CartListSerializer(ListSerializer):
    __product_fields = ['product_id', 'product_name', 'image']

    def to_representation(self, data):
        initial_results = super().to_representation(data)

        index_mapping = {}
        for index, result in enumerate(initial_results):
            product_id = result['product_id']
            if product_id in index_mapping:
                index_mapping[product_id].append(index)
            else:
                index_mapping[product_id] = [index]

        results = []
        for indexes in index_mapping.values():
            result = {}

            for field in self.__product_fields:
                result[field] = initial_results[indexes[0]][field]

            result['carts'] = []

            for index in indexes:
                for field in self.__product_fields:
                    initial_results[index].pop(field)

                result['carts'].append(initial_results[index])

            results.append(result)

        return results

    def validate(self, attrs):
        if self.instance is None:
            shopper = self.context['shopper']
            options = [attr['option'] for attr in attrs]
            if shopper.carts.exclude(option__in=options).count() + len(attrs) > ORDER_MAXIMUM_NUMBER:
                raise ValidationError('exceeded the maximum number({}).'.format(ORDER_MAXIMUM_NUMBER))
        
        return attrs

    def create(self, validated_data):
        shopper = self.context['shopper']

        input_data = {}
        for data in validated_data:
            input_data[data['option'].id] = data
            input_data[data['option'].id].pop('option')

        existing_option_id = list(shopper.carts.all().values_list('option__id', flat=True))
        input_option_id = input_data.keys()
        
        create_option_id = set(input_option_id) - set(existing_option_id)
        update_option_id = set(input_option_id) - set(create_option_id)

        for option_id in update_option_id:
            cart = shopper.carts.get(option_id=option_id)
            cart.count += input_data[option_id]['count']
            cart.save()

        carts = [self.child.Meta.model(shopper=shopper, option_id=option_id, **input_data[option_id]) for option_id in create_option_id]
        return self.child.Meta.model.objects.bulk_create(carts)


class CartSerializer(ModelSerializer):
    product_name = CharField(read_only=True, source='option.product_color.product.name')
    base_discounted_price = IntegerField(read_only=True, source='option.product_color.product.base_discounted_price')
    display_color_name = CharField(read_only=True, source='option.product_color.display_color_name')
    size = CharField(read_only=True, source='option.size')
    product_id = IntegerField(read_only=True, source='option.product_color.product.id')

    class Meta:
        model = Cart
        exclude = ['shopper', 'created_at']
        extra_kwargs = {
            'count': {'min_value': 1, 'max_value': 100}, 
        }
        list_serializer_class = CartListSerializer

    def to_representation(self, instance):
        result = super().to_representation(instance)

        result['base_discounted_price'] *= result['count'] 
        if instance.option.product_color.product.images.all().exists():
            result['image'] = BASE_IMAGE_URL + instance.option.product_color.product.images.all()[0].image_url
        else:
            result['image'] = DEFAULT_IMAGE_URL

        return result


class BuildingSerializer(ModelSerializer):
    floors = StringRelatedField(many=True)

    class Meta:
        model = Building
        exclude = ['id']


class UserPasswordSerializer(Serializer):
    current_password = CharField(min_length=10, max_length=128)
    new_password = RegexField(PASSWORD_REGEX, max_length=128, min_length=10)

    def validate(self, attrs):
        if not self.instance.check_password(attrs['current_password']):
            raise ValidationError('current password does not correct.')
        elif attrs['current_password'] == attrs['new_password']:
            raise ValidationError('new password is same as the current password.')
    
        PasswordSimilarityValidator().validate(attrs['new_password'], self.instance.username)

        return attrs

    def __discard_refresh_token(self, user_id):
        discarding_tokens = OutstandingToken.objects.filter(user_id=user_id, expires_at__gt=timezone.now(), blacklistedtoken__isnull=True).all()
        BlacklistedToken.objects.bulk_create([BlacklistedToken(token=token) for token in discarding_tokens])

    def update(self, instance, validated_data):
        instance.password = validated_data['new_password']
        instance.save(update_fields=['password'])
        self.__discard_refresh_token(instance.id)
        
        return instance


class ShopperShippingAddressSerializer(ModelSerializer):
    name = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=20, required=False)
    receiver_name = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=20)
    receiver_mobile_number = RegexField(MOBILE_NUMBER_REGEX)
    receiver_phone_number = RegexField(PHONE_NUMBER_REGEX, required=False)
    zip_code = RegexField(ZIP_CODE_REGEX)
    detail_address = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=100)

    class Meta:
        model = ShopperShippingAddress
        exclude = ['shopper']
        extra_kwargs = {
            'shopper': {'read_only': True},
        }


class PointHistorySerializer(ModelSerializer):
    order_number = CharField(read_only=True,  source='order.number')

    class Meta:
        model = PointHistory
        exclude = ['shopper', 'order']