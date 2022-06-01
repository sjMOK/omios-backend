from django.db.models import Q
from django.db.models.query import Prefetch
from django.db.transaction import atomic

from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.permissions import AllowAny

from common.utils import get_response
from user.models import Shopper
from product.models import ProductImage
from .models import Order, OrderItem, StatusHistory
from .serializers import (
    OrderSerializer, OrderWriteSerializer, OrderItemWriteSerializer, ShippingAddressSerializer, 
    CancellationInformationSerializer, StatusHistorySerializer, OrderConfirmSerializer, DeliverySerializer
)
from .permissions import OrderPermission, OrderItemPermission


from django.db import connection


class OrderViewSet(GenericViewSet):
    pagination_class = None
    permission_classes = [OrderPermission]
    lookup_field = 'id'
    lookup_url_kwarg = 'order_id'

    def get_serializer_class(self):
        if self.action in ['create']:
            return OrderWriteSerializer
        elif self.action == 'update_shipping_address':
            return ShippingAddressSerializer
        elif self.action == 'confirm':
            return OrderConfirmSerializer
        elif self.action == 'delivery':
            return DeliverySerializer
        
        return OrderSerializer

    def __get_conditions(self):
        conditions = Q()
        if self.action == 'list':
            conditions = Q(shopper_id=self.request.user.id)

        return conditions

    def get_queryset(self):
        queryset = Order.objects
        if self.action in ['list', 'retrieve']:
            image = ProductImage.objects.filter(sequence=1)
            items = OrderItem.objects.select_related('option__product_color__product', 'status').prefetch_related(Prefetch('option__product_color__product__images', queryset=image))
            queryset = queryset.select_related('shipping_address').prefetch_related(Prefetch('items', queryset=items))

        return queryset.filter(self.__get_conditions())

    def list(self, request):
        return get_response(data=self.get_serializer(self.get_queryset(), many=True).data)        

    @atomic
    def create(self, request):
        shopper = Shopper.objects.select_related('membership').get(user=request.user)
        serializer = self.get_serializer(data=request.data, context={'shopper': shopper})

        serializer.is_valid(raise_exception=True)

        # todo
        # 결제 로직 + 결제 관련 상태 (입금 대기 or 결제 완료)

        order = serializer.save(status_id=101)

        return get_response(status=HTTP_201_CREATED, data={'id': order.id})
    
    def retrieve(self, request, order_id):
        return get_response(data=self.get_serializer(self.get_object()).data)

    @action(['put'], True, 'shipping-address')
    def update_shipping_address(self, request, order_id):
        serializer = self.get_serializer(data=request.data, context={'order': self.get_object()})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return get_response(data={'id': int(order_id)})

    @atomic
    @action(['post'], False, 'confirm', permission_classes=[AllowAny])
    def confirm(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return get_response(status=HTTP_201_CREATED, data=serializer.save())

    @atomic
    @action(['post'], False, 'delivery', permission_classes=[AllowAny])
    def delivery(self, request):
        if len(request.data) > 50:
            return get_response(status=HTTP_400_BAD_REQUEST, message='You can only request up to 50 at a time.')

        serializer = self.get_serializer(data=request.data, many=True, allow_empty=False)
        serializer.is_valid(raise_exception=True)
        
        return get_response(status=HTTP_201_CREATED, data=serializer.save())


class OrderItemViewSet(GenericViewSet):
    pagination_class = None
    permission_classes = [OrderItemPermission]
    serializer_class = OrderItemWriteSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'item_id'
    __patchable_fields = set(['option'])
 
    def get_queryset(self):
        return OrderItem.objects.select_related('order', 'option__product_color')

    def partial_update(self, request, item_id):
        if set(request.data).difference(self.__patchable_fields):
            return get_response(status=HTTP_400_BAD_REQUEST, message='It contains requests for fields that do not exist or cannot be modified.')

        serializer = self.get_serializer(self.get_object(), request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return get_response(data={'id': int(item_id)})


class ClaimViewSet(GenericViewSet):
    permission_classes = [OrderPermission]

    def get_serializer_class(self):
        if self.action == 'cancel':
            return CancellationInformationSerializer

    def __get_context(self, status_id):
        return {
            'shopper': self.request.user.shopper,
            'order_id': int(self.kwargs['order_id']),
            'status_id': status_id,
        }

    @action(['post'], False)
    def cancel(self, request, order_id):
        serializer = self.get_serializer(data=request.data, context=self.__get_context([100, 101]))
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': request.data['order_items']})

    # todo
    # 교환 요청, 교환 요청 철회, 교환 완료, 교환 수락, 교환 거부
    # 반품 요청, 반품 요청 철회, 반품 완료, 반품 수락, 반품 거부


class StatusHistoryAPIView(GenericAPIView):
    pagination_class = None
    permission_classes = [OrderItemPermission]
    serializer_class = StatusHistorySerializer

    def get_queryset(self):
        order_item = get_object_or_404(OrderItem.objects.select_related('order'), id=self.kwargs['item_id'])
        self.check_object_permissions(self.request, order_item)
        
        return StatusHistory.objects.select_related('status').filter(order_item=order_item)

    def get(self, request, item_id):
        return get_response(data=self.get_serializer(self.get_queryset(), many=True).data)
