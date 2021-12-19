from random import randint
from difflib import SequenceMatcher
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import RegexField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch
from rest_framework.validators import UniqueValidator

from . import models

class UserAccessTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        if hasattr(user, 'shopper'):
            token['user_type'] = 'shopper'
        elif hasattr(user, 'wholesaler'):
            token['user_type'] = 'wholesaler'

        models.OutstandingToken.objects.filter(jti=token['jti']).update(
            token = token,
        )
        
        return token


class UserRefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = super().validate(attrs)
        refresh = RefreshToken(token['refresh'])
    
        models.OutstandingToken.objects.create(
            user=models.User.objects.get(id=refresh['user_id']),
            jti=refresh['jti'],
            token=str(refresh),
            created_at=refresh.current_time,
            expires_at=datetime_from_epoch(refresh['exp']),
        )
        
        return token


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Membership
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    username = RegexField(r'^[a-zA-Z0-9]+$', min_length=4, max_length=30)
    password = RegexField(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[!-~]+$', max_length=128, min_length=10)
    phone = RegexField(r'^01[0|1|6|7|8|9][0-9]{7,8}$')

    class Meta:
        model = models.User
        fields = '__all__'

    def __init__(self, max_similarity=0.5):
        super().__init__()
        self.max_similarity = max_similarity

    def validate(self, data):
        if SequenceMatcher(a=data['password'], b=data['username']).quick_ratio() >= self.max_similarity:
            raise serializers.ValidationError('The similarity between password and username is too large.')
        elif SequenceMatcher(a=data['password'], b=data['email']).quick_ratio() >= self.max_similarity:
            raise serializers.ValidationError('The similarity between password and email is too large.')

        return data

    
class ShopperSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    name = RegexField(r'^[가-힣]+$', max_length=20)
    nickname = RegexField(r'^[a-z0-9._]+$', min_length=4, max_length=20, required=False, validators=[UniqueValidator(queryset=models.Shopper.objects.all())])
    zipcode = RegexField(r'^[0-9]{5}$', max_length=5)

    class Meta:
        model = models.Shopper
        fields = '__all__'
        extra_kwargs = {            
            'height': {'min_value': 100, 'max_value': 250},
            'weight': {'min_value': 30, 'max_value': 200}
        }

    def __get_random_nickname(self):
        while True:
            nickname = 'dp_' + timezone.now().strftime('%m%d%H%M') + '_' + str(randint(1, 10**5))
            if not models.Shopper.objects.filter(nickname=nickname).exists():
                return nickname

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = models.User.objects.create_user(**user_data)
        nickname = self.__get_random_nickname()
        shopper = models.Shopper.objects.create(user=user, nickname=nickname, **validated_data)
        
        return shopper

    def update(self, instance, validated_data):
        user = instance.user
        user_data = validated_data.pop('user')

        for key, value in user_data.items():
            if key == 'password':
                user.set_password(value)
                continue
            
            setattr(user, key, value)
        user.save()

        for key ,value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        return instance


class WholesalerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.Wholesaler
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = models.User.objects.create_user(**user_data)
        wholesaler = models.Wholesaler.objects.create(user=user, **validated_data)
        
        return wholesaler


class UserPasswordSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    current_password = serializers.CharField(min_length=10, max_length=128)
    new_password = serializers.RegexField(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[!-~]+$', max_length=128, min_length=10)

    def __init__(self, max_similarity=0.5):
        super().__init__()
        self.max_similarity = max_similarity

    def validate(self, data):
        user = models.User.objects.get(id=data['id'])
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError('new password is same as the current password.')
        elif not user.check_password(data['current_password']):
            raise serializers.ValidationError('current password does not correct.')
        elif SequenceMatcher(a=data['new_password'], b=user.username).quick_ratio() >= self.max_similarity:
            raise serializers.ValidationError('The similarity between password and username is too large.')
        elif SequenceMatcher(a=data['new_password'], b=user.email).quick_ratio() >= self.max_similarity:
            raise serializers.ValidationError('The similarity between password and email is too large.')

        return data        
