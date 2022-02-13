from rest_framework.serializers import *
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from common import documentation
from . import models, serializers, views


class TokenRequest(serializers.UserAccessTokenSerializer):
    pass


class RefreshTokenRequest(serializers.UserRefreshTokenSerializer):
    pass


class ShopperCreateRequest(serializers.ShopperSerializer):
    class Meta:
        model = models.Shopper
        fields = ['username', 'password', 'email', 'phone', 'name', 'birthday', 'gender']


class ShopperUpdateRequest(serializers.ShopperSerializer):
    class Meta:
        model = models.Shopper
        fields = ['email', 'nickname', 'height', 'weight']
        extra_kwargs = {'email': {'required': False}}


class PasswordUpdateRequest(serializers.UserPasswordSerializer):
    def __init__(self):
        super(serializers.UserPasswordSerializer, self).__init__()


class UniqueRequest(Serializer):
    username = CharField(required=False)
    shopper_nickname = CharField(required=False)
    wholesaler_name = CharField(required=False)
    wholesaler_company_registration_number = CharField(required=False)


class Token(serializers.UserRefreshTokenSerializer):
    access = CharField()


class Shopper(ModelSerializer):
    membership = serializers.MembershipSerializer()
    class Meta:
        model = models.Shopper
        exclude = ['password']
        extra_kwargs = {
            'is_admin': {'required': True},
            'is_active': {'required': True},
        }


class DecoratedUserRefreshTokenView(views.UserRefreshTokenView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoreatedWholesalerDetailView(views.WholesalerDetailView):
    def get(self, request):
        return super().get(request)

    def post(self, request):
        return super().post(request)

    def patch(self, request):
        return super().patch(request)

    def delete(self, request):
        return super().delete(request)


decorated_access_token_view = swagger_auto_schema(
    method='POST', request_body=TokenRequest, **documentation.get_response(Token(), 201), security=[], operation_description='id, password로 토큰 발급 (로그인)'
)(views.UserAccessTokenView.as_view())

decorated_refresh_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshTokenRequest, **documentation.get_response(Token(), 201), security=[], operation_description='refresh 토큰으로 토큰 발급'
)(views.UserRefreshTokenView.as_view())

decorated_blacklist_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshTokenRequest, **documentation.get_response(code=201), operation_description='refresh 토큰 폐기 (로그아웃)'
)(views.UserBlacklistTokenView.as_view())

decorated_shopper_view = swagger_auto_schema(
    method='GET', **documentation.get_response(Shopper()), operation_description='Shopper 데이터 가져오기'
)(swagger_auto_schema(
    method='POST', request_body=ShopperCreateRequest, **documentation.get_response(code=201), security=[], operation_description='Shopper 회원가입'
)(swagger_auto_schema(
    method='PATCH', request_body=ShopperUpdateRequest, **documentation.get_response(), operation_description='Shopper 회원정보 수정'
)(swagger_auto_schema(
    method='DELETE', **documentation.get_response(), operation_description='Shopper 회원탈퇴'
)(views.ShopperDetailView.as_view()))))

decorated_wholesaler_view = swagger_auto_schema(
    method='GET', **documentation.get_response(Shopper()), operation_description='Wholesaler 데이터 가져오기'
)(swagger_auto_schema(
    method='POST', request_body=ShopperCreateRequest, **documentation.get_response(code=201), security=[], operation_description='Wholesaler 회원가입'
)(swagger_auto_schema(
    method='PATCH', request_body=ShopperUpdateRequest, **documentation.get_response(), operation_description='Wholesaler 회원정보 수정'
)(swagger_auto_schema(
    method='DELETE', **documentation.get_response(), operation_description='Wholesaler 회원탈퇴'
)(views.WholesalerDetailView.as_view()))))

decorated_user_password_view = swagger_auto_schema(
    method='PATCH', request_body=PasswordUpdateRequest, **documentation.get_response(), operation_description='비밀번호 수정'
)(views.UserPasswordView.as_view())

decorated_is_unique_view = swagger_auto_schema(
    method='GET', query_serializer=UniqueRequest, **documentation.get_response(documentation.UniqueResponse()), security=[], operation_description='중복검사'
)(views.is_unique)
