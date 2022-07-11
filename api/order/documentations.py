from drf_yasg.utils import swagger_auto_schema
from rest_framework.serializers import Serializer, IntegerField, ListField, ImageField, CharField, DateField
from rest_framework.decorators import action

from common.permissions import IsEasyAdminUser
from common.documentations import get_response, get_ids_response, get_paginated_response
from product.serializers import OptionInOrderItemSerializer
from .serializers import (
    OrderSerializer, OrderWriteSerializer, OrderItemSerializer, OrderItemStatisticsSerializer,
    StatusHistorySerializer, CancellationInformationSerializer, DeliverySerializer,
)
from .views import OrderViewSet, OrderItemViewSet, ClaimViewSet, StatusHistoryAPIView


class OrderQuerySerializer(Serializer):
    status = CharField(required=False, help_text='응답받은 한글 상태명을 그대로 입력')
    start_date = DateField(required=False, help_text='end_date와 함께 입력되지 않으면 무시\nformat="YYYY-mm-dd"')
    end_date = DateField(required=False, help_text='start_date와 함께 입력되지 않으면 무시\nformat="YYYY-mm-dd"')


class OptionInOrderItemResponse(OptionInOrderItemSerializer):
    product_image_url = ImageField()

    class Meta:
        ref_name = 'OptionInOrderItem'


class OrderItemResponse(OrderItemSerializer):
    option = OptionInOrderItemResponse()

    class Meta(OrderItemSerializer.Meta):
        ref_name = 'OrderItem'


class OrderResponse(OrderSerializer):
    items = OrderItemResponse(many=True)

    class Meta(OrderSerializer.Meta):
        ref_name = 'Order'


class OrderCreateRequest(OrderWriteSerializer):
    class Meta(OrderWriteSerializer.Meta):
        exclude = ['shopper', 'created_at']


class OptionInOrderItemUpdate(Serializer):
    option = IntegerField()


class OrderItemList(Serializer):
    order_items = ListField(child=IntegerField())


class OrderConfirmResponse(Serializer):
    success = ListField(child=IntegerField())
    nonexistence = ListField(child=IntegerField())
    not_requestable_status = ListField(child=IntegerField())


class DeliveryResponse(Serializer):
    success = ListField(child=IntegerField())
    invalid_orders = ListField(child=IntegerField())
    existed_invoice = ListField(child=IntegerField())


class DecoratedOrderViewSet(OrderViewSet):
    create_description = '''
        주문 생성

        --- discont --- : 할인할 금액에 해당하는 필드
        --- discounted --- : 할인이 적용된 금액에 해당하는 필드

        shopper_coupon, coupon_discount_price 필드를 함께 보내지 않으면 에러 반환

        금액 계산은 정책 명세서에 작성되어 있는 내용 기반
        items 내의 금액 필드는 적립금 적용을 제외한 금액
    '''

    @swagger_auto_schema(query_serializer=OrderQuerySerializer, **get_paginated_response(OrderResponse(many=True)), operation_description='주문 목록 조회')
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=OrderCreateRequest, **get_response(code=201), operation_description=create_description)
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(**get_response(OrderResponse()), operation_description='주문 단건 조회')
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_auto_schema(**get_response(), operation_description='주문 배송지 변경\n입금 대기, 결제 완료 상태인 주문만 배송지 변경 가능')
    @action(['put'], True, 'shipping-address')
    def update_shipping_address(self, *args, **kwargs):
        return super().update_shipping_address(*args, **kwargs)

    @swagger_auto_schema(request_body=OrderItemList, **get_response(OrderConfirmResponse()), security=[], operation_description='이지어드민 기능\n발주 확인')
    @action(['post'], False, 'confirm', permission_classes=[IsEasyAdminUser])
    def confirm(self, *args, **kwargs):
        return super().confirm(*args, **kwargs)

    @swagger_auto_schema(request_body=DeliverySerializer(many=True), **get_response(DeliveryResponse()), security=[], operation_description='이지어드민 기능\n송장 입력')
    @action(['post'], False, 'delivery', permission_classes=[IsEasyAdminUser])
    def delivery(self, *args, **kwargs):
        return super().delivery(*args, **kwargs)

class DecoratedOrderItemViewSet(OrderItemViewSet):
    @swagger_auto_schema(request_body=OptionInOrderItemUpdate, **get_response(), operation_description='주문 항목 옵션 변경\n입금 대기, 결제 완료 상태인 주문만 옵션 변경 가능')
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_auto_schema(**get_response(OrderItemStatisticsSerializer(many=True)), operation_description='상태별 주문 개수 조회 (정상인 6개 상태)')
    @action(['get'], False, 'statistics')
    def get_statistics(self, *args, **kwargs):
        return super().get_statistics(*args, **kwargs)

class DecoratedClaimViewset(ClaimViewSet):
    cancel_description = '''
        주문 취소 기능
        하나의 주문에 있는 항목들에 대해서만 취소 가능
        입금 대기, 결제 완료 상태인 주문만 취소 가능
    '''
    @swagger_auto_schema(request_body=OrderItemList, **get_ids_response(201), operation_description=cancel_description)
    @action(['post'], False)
    def cancel(self, *args, **kwargs):
        super().cancel(*args, **kwargs)


decorated_status_history_view = swagger_auto_schema(
    method='GET', **get_response(StatusHistorySerializer(many=True), 200), operation_description='주문 항목 상태 조회'
)(StatusHistoryAPIView.as_view())