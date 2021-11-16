from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import datetime_from_epoch

from . import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['username', 'password']


class ShopperSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.Shopper
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = models.User.objects.create_user(**user_data)
        shopper = models.Shopper.objects.create(user=user, **validated_data)
        return shopper


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


class UserAccessTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        if hasattr(user, 'shopper'):
            token['user_type'] = 'shopper'
        elif hasattr(user, 'wholesaler'):
            token['user_type'] = 'wholesaler'

        OutstandingToken.objects.filter(jti=token['jti']).update(
            token = token,
        )
        
        return token

class UserRefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = super().validate(attrs)
        refresh = RefreshToken(token['refresh'])
    
        OutstandingToken.objects.create(
            user=models.User.objects.get(id=refresh['user_id']),
            jti=refresh['jti'],
            token=str(refresh),
            created_at=refresh.current_time,
            expires_at=datetime_from_epoch(refresh['exp']),
        )
        
        return token
