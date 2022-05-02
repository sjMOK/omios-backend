from drf_yasg.utils import swagger_auto_schema
from rest_framework.serializers import Serializer, ModelSerializer, IntegerField, CharField
from rest_framework.decorators import action

from common.documentations import UniqueResponse, Image, get_response
from .models import Shopper, Wholesaler
from .serializers import (
    IssuingTokenSerializer, RefreshingTokenSerializer, MembershipSerializer, ShopperSerializer, ShopperShippingAddressSerializer, 
    WholesalerSerializer, UserPasswordSerializer, BuildingSerializer, PointHistorySerializer
)
from .views import (
    IssuingTokenView, RefreshingTokenView, BlacklistingTokenView, ShopperViewSet, WholesalerViewSet, ProductLikeView,
    ShopperShippingAddressViewSet,
    upload_business_registration_image, get_buildings, change_password, is_unique, get_point_histories,
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


class ProductLikeViewResponse(Serializer):
    shopper_id = IntegerField()
    product_id = IntegerField()


class DecoratedRefreshingTokenView(RefreshingTokenView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoratedShopperViewSet(ShopperViewSet):
    @swagger_auto_schema(**get_response(Shopper()), operation_description='Shopper 데이터 가져오기')
    def retrieve(self, request, user_id=None):
        return super().retrieve(request, user_id)

    @swagger_auto_schema(request_body=ShopperCreateRequest, **get_response(code=201), security=[], operation_description='Shopper 회원가입')
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=ShopperUpdateRequest, **get_response(), operation_description='Shopper 회원정보 수정')
    def partial_update(self, request, user_id=None):
        return super().partial_update(request, user_id)

    @swagger_auto_schema(**get_response(), operation_description='Shopper 회원탈퇴')
    def destroy(self, request, user_id=None):
        return super().destroy(request, user_id)


class DecoratedWholesalerViewSet(WholesalerViewSet):
    @swagger_auto_schema(**get_response(Wholesaler()), operation_description='Wholesaler 데이터 가져오기')
    def retrieve(self, request, user_id=None):
        return super().retrieve(request, user_id)

    @swagger_auto_schema(request_body=WholesalerCreateRequest, **get_response(code=201), security=[], operation_description='Wholesaler 회원가입')
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=WholesalerUpdateRequest, **get_response(), operation_description='Wholesaler 회원정보 수정')
    def partial_update(self, request, user_id=None):
        return super().partial_update(request, user_id)

    @swagger_auto_schema(**get_response(), operation_description='Wholesaler 회원탈퇴')
    def destroy(self, request, user_id=None):
        return super().destroy(request, user_id)


class DecoratedShopperShippingAddressViewSet(ShopperShippingAddressViewSet):
    @swagger_auto_schema(**get_response(ShopperShippingAddressSerializer(many=True)), operation_description='배송지 리스트 조회')
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=ShopperShippingAddressSerializer, **get_response(code=201), operation_description='배송지 생성\n최초로 등록하는 배송지는 자동으로 기본 배송지로 지정됨\n기본 배송지를 등록하는 경우 기존의 기본 배송지는 기본 배송지 플래그가 해제됨')
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(request_body=ShopperShippingAddressSerializer, **get_response(), operation_description='배송지 수정\n기본 배송지를 true로 수정하면 기존의 기본 배송지는 기본 배송지 플래그가 해제됨')
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_auto_schema(**get_response(), operation_description='배송지 삭제')
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)

    @swagger_auto_schema(**get_response(ShopperShippingAddressSerializer()), operation_description='기본 배송지 조회\n기본배송지로 지정된 배송지가 없다면 빈 딕셔너리({}) 반환')
    @action(methods=['GET'], detail=False, url_path='default')
    def get_default_address(self, *args, **kwargs):
        return super().get_default_address(*args, **kwargs)


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

decorated_product_like_view = swagger_auto_schema(
    method='POST', **get_response(ProductLikeViewResponse(), 201), operation_description='상품 좋아요 생성(좋아요 버튼 클릭시 요청)'
)(swagger_auto_schema(
    method='DELETE', **get_response(ProductLikeViewResponse()), operation_description='상품 좋아요 삭제(좋아요 버튼 한번 더 클릭시 요청)'
)(ProductLikeView.as_view()))

decorated_shopper_point_history_view = swagger_auto_schema(
    method='GET', **get_response(PointHistorySerializer()), operation_description='적립금 사용 내역 정보 가져오기'
)(get_point_histories)