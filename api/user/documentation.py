from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema

from common.documentation import UniqueResponse, get_response
from .models import Shopper
from .serializers import (
    Serializer, ModelSerializer, IssuingTokenSerializer, RefreshingTokenSerializer, 
    MembershipSerializer, ShopperSerializer, UserPasswordSerializer, CharField,
)
from .views import (
    IssuingTokenView, RefreshingTokenView, BlacklistingTokenView, 
    ShopperView, WholesalerView, is_unique, change_password,
)


class IssuingTokenRequest(IssuingTokenSerializer):
    pass


class RefreshingTokenRequest(RefreshingTokenSerializer):
    pass


class ShopperCreateRequest(ShopperSerializer):
    class Meta:
        model = Shopper
        fields = ['username', 'password', 'email', 'mobile_number', 'name', 'birthday', 'gender']


class ShopperUpdateRequest(ShopperSerializer):
    class Meta:
        model = Shopper
        fields = ['email', 'nickname', 'height', 'weight']
        extra_kwargs = {'email': {'required': False}}


class PasswordUpdateRequest(UserPasswordSerializer):
    def __init__(self):
        super(UserPasswordSerializer, self).__init__()


class UniqueRequest(Serializer):
    username = CharField(required=False)
    shopper_nickname = CharField(required=False)
    wholesaler_name = CharField(required=False)
    wholesaler_company_registration_number = CharField(required=False)


class Token(RefreshingTokenSerializer):
    access = CharField()


class Shopper(ModelSerializer):
    membership = MembershipSerializer()
    class Meta:
        model = Shopper
        exclude = ['password']
        extra_kwargs = {
            'is_admin': {'required': True},
            'is_active': {'required': True},
        }


class DecoratedRefreshingTokenView(RefreshingTokenView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoreatedWholesalerDetailView(WholesalerView):
    def get(self, request):
        return super().get(request)

    def post(self, request):
        return super().post(request)

    def patch(self, request):
        return super().patch(request)

    def delete(self, request):
        return super().delete(request)


decorated_issuing_token_view = swagger_auto_schema(
    method='POST', request_body=IssuingTokenRequest, **get_response(Token(), 201), security=[], operation_description='id, password로 토큰 발급 (로그인)'
)(IssuingTokenView.as_view())

decorated_refreshing_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshingTokenRequest, **get_response(Token(), 201), security=[], operation_description='refresh 토큰으로 토큰 발급'
)(DecoratedRefreshingTokenView.as_view())

decorated_blacklisting_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshingTokenRequest, **get_response(code=201), operation_description='refresh 토큰 폐기 (로그아웃)'
)(BlacklistingTokenView.as_view())

decorated_shopper_view = swagger_auto_schema(
    method='GET', **get_response(Shopper()), operation_description='Shopper 데이터 가져오기'
)(swagger_auto_schema(
    method='POST', request_body=ShopperCreateRequest, **get_response(code=201), security=[], operation_description='Shopper 회원가입'
)(swagger_auto_schema(
    method='PATCH', request_body=ShopperUpdateRequest, **get_response(), operation_description='Shopper 회원정보 수정'
)(swagger_auto_schema(
    method='DELETE', **get_response(), operation_description='Shopper 회원탈퇴'
)(ShopperView.as_view()))))

decorated_wholesaler_view = swagger_auto_schema(
    method='GET', **get_response(Shopper()), operation_description='Wholesaler 데이터 가져오기'
)(swagger_auto_schema(
    method='POST', request_body=ShopperCreateRequest, **get_response(code=201), security=[], operation_description='Wholesaler 회원가입'
)(swagger_auto_schema(
    method='PATCH', request_body=ShopperUpdateRequest, **get_response(), operation_description='Wholesaler 회원정보 수정'
)(swagger_auto_schema(
    method='DELETE', **get_response(), operation_description='Wholesaler 회원탈퇴'
)(WholesalerView.as_view()))))

decorated_user_password_view = swagger_auto_schema(
    method='PATCH', request_body=PasswordUpdateRequest, **get_response(), operation_description='비밀번호 수정'
)(change_password)

decorated_is_unique_view = swagger_auto_schema(
    method='GET', query_serializer=UniqueRequest, **get_response(UniqueResponse()), security=[], operation_description='중복검사'
)(is_unique)
