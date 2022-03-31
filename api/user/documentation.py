from drf_yasg.utils import swagger_auto_schema

from common.documentation import UniqueResponse, Image, get_response
from .models import Shopper, Wholesaler
from .serializers import (
    Serializer, ModelSerializer, IssuingTokenSerializer, RefreshingTokenSerializer, CharField, 
    MembershipSerializer, ShopperSerializer, WholesalerSerializer, UserPasswordSerializer, BuildingSerializer,
)
from .views import (
    IssuingTokenView, RefreshingTokenView, BlacklistingTokenView, ShopperViewSet, WholesalerViewSet,
    upload_business_registration_image, get_buildings, change_password, is_unique,
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


class WholesalerCreateRequest(WholesalerSerializer):
    class Meta:
        model = Wholesaler
        fields = [
            'username', 'password', 'name', 'company_registration_number', 'business_registration_image_url',
            'mobile_number', 'phone_number', 'email', 'zip_code', 'base_address', 'detail_address'
        ]


class WholesalerUpdateRequest(WholesalerSerializer):
    mobile_number = CharField(max_length=11, required=False)

    class Meta:
        model = Wholesaler
        fields = ['mobile_number', 'email']
        extra_kwargs = {
            'mobile_number': {'required': False},
            'email': {'required': False},
        }


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


class Wholesaler(ModelSerializer):
    class Meta:
        model = Wholesaler
        exclude = ['password']


class DecoratedRefreshingTokenView(RefreshingTokenView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoratedShopperViewSet(ShopperViewSet):
    @swagger_auto_schema(**get_response(Shopper()), operation_description='Shopper 데이터 가져오기')
    def retrieve(self, request, id=None):
        return super().retrieve(request, id)

    @swagger_auto_schema(request_body=ShopperCreateRequest, **get_response(code=201), security=[], operation_description='Shopper 회원가입')
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=ShopperUpdateRequest, **get_response(), operation_description='Shopper 회원정보 수정')
    def partial_update(self, request, id=None):
        return super().partial_update(request, id)

    @swagger_auto_schema(**get_response(), operation_description='Shopper 회원탈퇴')
    def destroy(self, request, id=None):
        return super().destroy(request, id)


class DecoratedWholesalerViewSet(WholesalerViewSet):
    @swagger_auto_schema(**get_response(Wholesaler()), operation_description='Wholesaler 데이터 가져오기')
    def retrieve(self, request, id=None):
        return super().retrieve(request, id)

    @swagger_auto_schema(request_body=WholesalerCreateRequest, **get_response(code=201), security=[], operation_description='Wholesaler 회원가입')
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=WholesalerUpdateRequest, **get_response(), operation_description='Wholesaler 회원정보 수정')
    def partial_update(self, request, id=None):
        return super().partial_update(request, id)

    @swagger_auto_schema(**get_response(), operation_description='Wholesaler 회원탈퇴')
    def destroy(self, request, id=None):
        return super().destroy(request, id)


decorated_issuing_token_view = swagger_auto_schema(
    method='POST', request_body=IssuingTokenRequest, **get_response(Token(), 201), security=[], operation_description='id, password로 토큰 발급 (로그인)'
)(IssuingTokenView.as_view())

decorated_refreshing_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshingTokenRequest, **get_response(Token(), 201), security=[], operation_description='refresh 토큰으로 토큰 발급'
)(DecoratedRefreshingTokenView.as_view())

decorated_blacklisting_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshingTokenRequest, **get_response(code=201), operation_description='refresh 토큰 폐기 (로그아웃)'
)(BlacklistingTokenView.as_view())

decorated_upload_business_registration_image_view = swagger_auto_schema(
    method='POST', request_body=Image, **get_response(Image(), 201), security=[], operation_description='사업자 등록증 이미지 업로드\n요청 시에는 파일 전체를 보내야 함\n응답 시에는 저장된 url을 반환'
)(upload_business_registration_image)

decorated_get_buildings_view = swagger_auto_schema(
    method='GET', **get_response(BuildingSerializer(many=True)), security=[], operation_description='동대문 건물 정보 가져오기'
)(get_buildings)

decorated_user_password_view = swagger_auto_schema(
    method='PATCH', request_body=PasswordUpdateRequest, **get_response(), operation_description='비밀번호 수정'
)(change_password)

decorated_is_unique_view = swagger_auto_schema(
    method='GET', query_serializer=UniqueRequest, **get_response(UniqueResponse()), security=[], operation_description='중복검사\n한 번에 하나의 파라미터에 대해서만 요청 가능'
)(is_unique)
