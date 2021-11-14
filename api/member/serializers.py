from .models import Shopper, Member, Wholesaler
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import datetime_from_epoch
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['username', 'password']


class ShopperSerializer(serializers.ModelSerializer):
    member = MemberSerializer()

    class Meta:
        model = Shopper
        fields = '__all__'

    def create(self, validated_data):
        member_data = validated_data.pop('member')
        member = Member.objects.create_user(**member_data)
        shopper = Shopper.objects.create(member=member, **validated_data)
        return shopper


class WholesalerSerializer(serializers.ModelSerializer):
    member = MemberSerializer()

    class Meta:
        model = Wholesaler
        fields = '__all__'

    def create(self, validated_data):
        member_data = validated_data.pop('member')
        member = Member.objects.create_user(**member_data)
        wholesaler = Wholesaler.objects.create(member=member, **validated_data)
        return wholesaler


class UserAccessTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, member):
        token = super().get_token(member)
        
        # todo : user 객체의 속성을 선택적으로 payload에 저장 (shopper_id or wholesaler_id)
        token['additional_data1'] = member.email

        OutstandingToken.objects.filter(jti=token['jti']).update(
            token = token,
        )
        
        return token

class UserRefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = super().validate(attrs)
        refresh = RefreshToken(token['refresh'])
    
        OutstandingToken.objects.create(
            user=User.objects.get(id=refresh['user_id']),
            jti=refresh['jti'],
            token=str(refresh),
            created_at=refresh.current_time,
            expires_at=datetime_from_epoch(refresh['exp']),
        )
        
        return token

        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "password", "username", "email")
