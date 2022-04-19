from django.utils import timezone

from rest_framework.serializers import (
    Serializer, ModelSerializer, ValidationError, IntegerField, CharField, RegexField, DateTimeField, StringRelatedField,
    BooleanField,
)
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, TokenBlacklistSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch

from common.utils import gmt_to_kst
from common.regular_expressions import (
    USERNAME_REGEX, PASSWORD_REGEX, NAME_REGEX, NICKNAME_REGEX, MOBILE_NUMBER_REGEX, PHONE_NUMBER_REGEX,
    BASIC_SPECIAL_CHARACTER_REGEX, ZIP_CODE_REGEX,
)
from .models import OutstandingToken, BlacklistedToken, ShopperShippingAddress, User, Shopper, Wholesaler
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
        
        if hasattr(user, 'shopper'):
            token['user_type'] = 'shopper'
        elif hasattr(user, 'wholesaler'):
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


class MembershipSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)


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


class BuildingSerializer(Serializer):
    name = CharField(read_only=True)
    zip_code = CharField(read_only=True)
    base_address = CharField(read_only=True)
    floors = StringRelatedField(many=True, read_only=True)


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


class ShopperShippingAddressSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=20, required=False)
    receiver_name = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=20)
    receiver_mobile_number = RegexField(MOBILE_NUMBER_REGEX)
    receiver_phone_number = RegexField(PHONE_NUMBER_REGEX, required=False)
    zip_code = RegexField(ZIP_CODE_REGEX)
    base_address = CharField(max_length=200)
    detail_address = RegexField(BASIC_SPECIAL_CHARACTER_REGEX, max_length=100)
    is_default = BooleanField()

    def create(self, validated_data):
        shopper = self.context['shopper']

        if validated_data['is_default'] and shopper.addresses.filter(is_default=True).exists():
            shopper.addresses.filter(is_default=True).update(is_default=False)

        if not validated_data['is_default'] and not shopper.addresses.all().exists():
            validated_data['is_default'] = True

        return ShopperShippingAddress.objects.create(shopper=self.context['shopper'], **validated_data)

    def update(self, instance, validated_data):
        shopper = self.context['shopper']

        is_default = validated_data.get('is_default', False)
        if is_default and shopper.addresses.filter(is_default=True).exists():
            shopper.addresses.filter(is_default=True).update(is_default=False)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save(update_fields=validated_data.keys())

        return instance
