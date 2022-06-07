from django.db import transaction

from drf_yasg.utils import swagger_auto_schema
from rest_framework.serializers import Serializer, ModelSerializer, IntegerField, CharField, URLField, ListField
from rest_framework.decorators import action

from common.documentations import UniqueResponse, Image, get_response
from .models import Shopper, Wholesaler
from .serializers import (
    IssuingTokenSerializer, RefreshingTokenSerializer, MembershipSerializer, ShopperSerializer, ShopperShippingAddressSerializer, 
    WholesalerSerializer, UserPasswordSerializer, BuildingSerializer, PointHistorySerializer
)
from .views import (
    IssuingTokenView, RefreshingTokenView, BlacklistingTokenView, ShopperView, WholesalerView, ProductLikeView,
    CartViewSet, ShopperShippingAddressViewSet,
    upload_business_registration_image, get_buildings, change_password, is_unique, get_point_histories,
)


class PasswordUpdateRequest(UserPasswordSerializer):
    def __init__(self):
        super(UserPasswordSerializer, self).__init__()


class UniqueRequest(Serializer):
    username = CharField(required=False)
    shopper_nickname = CharField(required=False)
    wholesaler_name = CharField(required=False)
    wholesaler_company_registration_number = CharField(required=False)


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


class CartCreateRequest(Serializer):
    option = IntegerField()
    count = IntegerField()


class CartUpdateRequest(Serializer):
    count = IntegerField()


class CartDeleteRequest(Serializer):
    id = ListField(child=IntegerField())


class TokenResponse(RefreshingTokenSerializer):
    access = CharField()


class ShopperResponse(ModelSerializer):
    membership = MembershipSerializer()
    class Meta:
        model = Shopper
        exclude = ['password']


class WholesalerResponse(ModelSerializer):
    class Meta:
        model = Wholesaler
        exclude = ['password']


class ProductCartResponse(Serializer):
    class CartResponse(Serializer):
            id = IntegerField()
            base_discounted_price = IntegerField()
            display_color_name = CharField()
            size = CharField()
            count = IntegerField()
            option = IntegerField()

    product_id = IntegerField()
    product_name = CharField()
    image = URLField()
    carts  =CartResponse(many=True)


class CartCreateResponse(Serializer):
    option_id = ListField(child=IntegerField())


class CartListResponse(Serializer):
    results = ProductCartResponse(many=True)
    total_sale_price = IntegerField()
    total_base_discounted_price = IntegerField()


class ProductLikeViewResponse(Serializer):
    shopper_id = IntegerField()
    product_id = IntegerField()


class DecoratedShopperView(ShopperView):
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    def patch(self, *args, **kwargs):
        return super().patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)


class DecoratedWholesalerView(WholesalerView):
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    def patch(self, *args, **kwargs):
        return super().patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)


class DecoratedRefreshingTokenView(RefreshingTokenView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoratedCartViewSet(CartViewSet):
    @swagger_auto_schema(**get_response(CartListResponse()), operation_description='장바구니 리스트 조회')
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=CartCreateRequest(many=True), **get_response(CartCreateResponse()), operation_description='장바구니 항목 등록\n최대 100개까지 등록 가능')
    @transaction.atomic
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(request_body=CartUpdateRequest, **get_response(), operation_description='장바구니 항목 업데이트\n업데이트는 수량만 가능')
    @transaction.atomic
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_auto_schema(request_body=CartDeleteRequest, **get_response(CartDeleteRequest()), operation_description='장바구니 항목 삭제\n다중 삭제 지원(id 배열을 request body에 전송)\n사용자 소유가 아닌 장바구니 항목 id 전송 시 PermissionDenied(403) 반환')
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def remove(self, *args, **kwargs):
        return super().remove(*args, **kwargs)


class DecoratedShopperShippingAddressViewSet(ShopperShippingAddressViewSet):
    @swagger_auto_schema(**get_response(ShopperShippingAddressSerializer(many=True)), operation_description='배송지 리스트 조회')
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=ShopperShippingAddressSerializer, **get_response(code=201), operation_description='배송지 생성\n최초로 등록하는 배송지는 자동으로 기본 배송지로 지정됨\n기본 배송지를 등록하는 경우 기존의 기본 배송지는 기본 배송지 플래그가 해제됨')
    @transaction.atomic
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(request_body=ShopperShippingAddressSerializer, **get_response(), operation_description='배송지 수정\n기본 배송지를 true로 수정하면 기존의 기본 배송지는 기본 배송지 플래그가 해제됨')
    @transaction.atomic
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_auto_schema(**get_response(), operation_description='배송지 삭제')
    @transaction.atomic
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)

    @swagger_auto_schema(**get_response(ShopperShippingAddressSerializer()), operation_description='기본 배송지 조회\n기본배송지로 지정된 배송지가 없다면 빈 딕셔너리({}) 반환')
    @action(methods=['GET'], detail=False, url_path='default')
    def get_default_address(self, *args, **kwargs):
        return super().get_default_address(*args, **kwargs)


decorated_issuing_token_view = swagger_auto_schema(
    method='POST', request_body=IssuingTokenRequest, **get_response(TokenResponse(), 201), security=[], operation_description='id, password로 토큰 발급 (로그인)'
)(IssuingTokenView.as_view())

decorated_refreshing_token_view = swagger_auto_schema(
    method='POST', request_body=RefreshingTokenRequest, **get_response(TokenResponse(), 201), security=[], operation_description='refresh 토큰으로 토큰 발급'
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

decorated_shopper_view = swagger_auto_schema(
    method='GET', **get_response(ShopperResponse()), operation_description='Shopper 데이터 가져오기'
)(swagger_auto_schema(
    method='POST', request_body=ShopperCreateRequest, **get_response(code=201), security=[], operation_description='Shopper 회원가입'
)(swagger_auto_schema(
    method='PATCH', request_body=ShopperUpdateRequest, **get_response(), operation_description='Shopper 회원정보 수정'
)(swagger_auto_schema(
    method='DELETE', **get_response(), operation_description='Shopper 회원탈퇴'
)(DecoratedShopperView.as_view()))))

decorated_wholesaler_view = swagger_auto_schema(
    method='GET', **get_response(WholesalerResponse()), operation_description='Wholesaler 데이터 가져오기'
)(swagger_auto_schema(
    method='POST', request_body=WholesalerCreateRequest, **get_response(code=201), security=[], operation_description='Wholesaler 회원가입'
)(swagger_auto_schema(
    method='PATCH', request_body=WholesalerUpdateRequest, **get_response(), operation_description='Wholesaler 회원정보 수정'
)(swagger_auto_schema(
    method='DELETE', **get_response(), operation_description='Wholesaler 회원탈퇴'
)(DecoratedWholesalerView.as_view()))))

decorated_product_like_view = swagger_auto_schema(
    method='POST', **get_response(ProductLikeViewResponse(), 201), operation_description='상품 좋아요 생성(좋아요 버튼 클릭시 요청)'
)(swagger_auto_schema(
    method='DELETE', **get_response(ProductLikeViewResponse()), operation_description='상품 좋아요 삭제(좋아요 버튼 한번 더 클릭시 요청)'
)(ProductLikeView.as_view()))

decorated_shopper_point_history_view = swagger_auto_schema(
    method='GET', **get_response(PointHistorySerializer()), operation_description='적립금 사용 내역 정보 가져오기'
)(get_point_histories)
