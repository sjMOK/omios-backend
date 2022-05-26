from drf_yasg.utils import swagger_auto_schema
from rest_framework.serializers import Serializer, IntegerField, ListField, ImageField
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from common.documentations import get_response, get_ids_response
from product.serializers import OptionInOrderItemSerializer
from .serializers import (
    OrderSerializer, OrderWriteSerializer, OrderItemSerializer, StatusHistorySerializer,
    CancellationInformationSerializer,
)
from .views import OrderViewSet, OrderItemViewSet, ClaimViewSet, StatusHistoryAPIView


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


class OrderConfirm(Serializer):
    success = ListField(child=IntegerField())
    nonexistence = ListField(child=IntegerField())
    not_requestable_status = ListField(child=IntegerField())


class DecoratedOrderViewSet(OrderViewSet):
    @swagger_auto_schema(**get_response(OrderResponse(many=True)), operation_description='주문 목록 조회')
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=OrderCreateRequest, **get_response(code=201), operation_description='주문 생성')
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(**get_response(OrderResponse()), operation_description='주문 단건 조회')
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_auto_schema(**get_response(), operation_description='주문 배송지 변경\n입금 대기, 결제 완료 상태인 주문만 배송지 변경 가능')
    @action(['put'], True, 'shipping-address')
    def update_shipping_address(self, *args, **kwargs):
        return super().update_shipping_address(*args, **kwargs)

    @swagger_auto_schema(request_body=OrderItemList, **get_response(OrderConfirm()), security=[], operation_description='이지어드민 기능\n발주 확인')
    @action(['post'], False, 'confirm', permission_classes=[AllowAny])
    def confirm(self, *args, **kwargs):
        return super().confirm(*args, **kwargs)


class DecoratedOrderItemViewSet(OrderItemViewSet):
    @swagger_auto_schema(request_body=OptionInOrderItemUpdate, **get_response(), operation_description='주문 항목 옵션 변경\n입금 대기, 결제 완료 상태인 주문만 옵션 변경 가능')
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)


class DecoratedClaimViewset(ClaimViewSet):
    cancel_discription = '''
        주문 취소 기능
        하나의 주문에 있는 항목들에 대해서만 취소 가능
        입금 대기, 결제 완료 상태인 주문만 취소 가능
    '''
    @swagger_auto_schema(request_body=OrderItemList, **get_ids_response(201), operation_description=cancel_discription)
    @action(['post'], False)
    def cancel(self, *args, **kwargs):
        super().cancel(*args, **kwargs)


decorated_status_history_view = swagger_auto_schema(
    method='GET', **get_response(StatusHistorySerializer(many=True), 200), operation_description='주문 항목 상태 조회'
)(StatusHistoryAPIView.as_view())