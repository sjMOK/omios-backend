from django.db.models import Q
from django.db.models.query import Prefetch

from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.exceptions import APIException

from common.utils import get_response
from common.exceptions import BadRequestError
from user.models import Shopper
from product.models import Product, ProductImage, Option
from .models import (
    Order, OrderItem, ShippingAddress, Status, StatusHistory,
)
from .serializers import (
    OrderItemSerializer, OrderSerializer, OrderWriteSerializer, OrderItemWriteSerializer, 
    ShippingAddressSerializer, CancellationInformationSerializer, StatusHistorySerializer,
)
from .permissions import OrderPermission, OrderItemPermission

from rest_framework.permissions import AllowAny
from django.db import connection
from django.forms import model_to_dict

class OrderViewSet(GenericViewSet):
    permission_classes = [OrderPermission]
    lookup_field = 'id'
    lookup_url_kwarg = 'order_id'
    __actions_requiring_write_serilaizer = ['create', 'partial_update']
    __patchable_fields = ['shipping_address']

    def get_serializer_class(self):
        # if self.action in self.__actions_requiring_write_serilaizer:
        #     return OrderWriteSerializer

        if self.action in ['create']:
            return OrderWriteSerializer
        elif self.action == 'update_shipping_address':
            return ShippingAddressSerializer
        
        return OrderSerializer

    def get_queryset(self):
        if self.request.user.is_wholesaler:
            pass
        elif self.request.user.is_shopper:
            condition = Q(shopper_id=self.request.user.id)
        else:
            raise APIException('Unrecognized user.')

        image = ProductImage.objects.filter(sequence=1)
        items = OrderItem.objects.select_related('option__product_color__product', 'status').prefetch_related(Prefetch('option__product_color__product__images', queryset=image))
        
        return Order.objects.select_related('shipping_address').prefetch_related(Prefetch('items', queryset=items)).filter(condition)

    def list(self, request):
        return get_response(data=self.get_serializer(self.get_queryset(), many=True).data)        

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
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        serializer.save()

        return get_response(data={'id': order_id})


class OrderItemViewSet(GenericViewSet):
    permission_classes = [OrderItemPermission]
    serializer_class = OrderItemWriteSerializer
    # queryset = OrderItem
    lookup_field = 'id'
    lookup_url_kwarg = 'item_id'
    __patchable_fields = set(['option'])
 
    def get_queryset(self):
        if hasattr(self.request.user, 'shopper'):
            condition = Q(order__shopper=self.request.user.shopper)
        else:
            raise APIException('Unrecognized user.')

        if 'order' in self.request.data:
            condition &= Q(order_id=self.request.data['order'])
        if 'items' in self.request.data:
            condition &= Q(id__in=self.request.data['items'])

        return OrderItem.objects.select_related('order', 'option__product_color').filter(condition)

    def partial_update(self, request, item_id):
        if set(request.data).difference(self.__patchable_fields):
            return get_response(status=HTTP_400_BAD_REQUEST, message='It contains requests for fields that do not exist or cannot be modified.')

        serializer = self.get_serializer(self.get_object(), request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return get_response(data={'id': item_id})

    # todo 발주확인 관련


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
    permission_classes = [OrderItemPermission]
    serializer_class = StatusHistorySerializer

    def get_queryset(self):
        order_item = get_object_or_404(OrderItem.objects.select_related('order'), id=self.kwargs['item_id'])
        self.check_object_permissions(self.request, order_item)
        
        return StatusHistory.objects.filter(order_item=order_item)

    def get(self, request, item_id):
        return get_response(data=self.get_serializer(self.get_queryset(), many=True).data)