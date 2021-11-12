from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from datetime import datetime

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
            expires_at=datetime.utcfromtimestamp(refresh['exp']),
        )
        
        return token

        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "password", "username", "email")