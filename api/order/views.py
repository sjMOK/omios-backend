from django.db.models import Q
from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.exceptions import APIException

from common.utils import get_response
from product.models import Product, ProductImage, Option
from .models import (
    Order, OrderItem, ShippingAddress, Status,
)
from .serializers import (
    OrderSerializer, OrderWriteSerializer, OrderItemWriteSerializer, ShippingAddressSerializer
)
from .permissions import OrderPermission, OrderItemPermission

from rest_framework.permissions import AllowAny
from django.db import connection
from django.forms import model_to_dict

class OrderViewSet(GenericViewSet):
    permission_classes = [OrderPermission]
    lookup_field = 'id'
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
        if hasattr(self.request.user, 'wholesaler'):
            pass
        elif hasattr(self.request.user, 'shopper'):
            condition = Q(shopper=self.request.user.shopper)
        else:
            raise APIException('Unrecognized user.')

        image = ProductImage.objects.filter(sequence=1)
        items = OrderItem.objects.select_related('option__product_color__product', 'status').prefetch_related(Prefetch('option__product_color__product__images', queryset=image))
        
        return Order.objects.select_related('shipping_address').prefetch_related(Prefetch('items', queryset=items)).filter(condition)

    def list(self, request):
        return get_response(data=self.get_serializer(self.get_queryset(), many=True).data)        

    def create(self, request):
        serializer = self.get_serializer(data=request.data, context={'shopper': request.user.shopper})

        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        # todo
        # 결제 로직 + 결제 관련 상태 (입금 대기 or 결제 완료 or 결제 오류)

        order = serializer.save(status_id=101)

        # return get_response(data={'id': order.id})
        return get_response(data=connection.queries)
    
    def retrieve(self, request, id):
        return get_response(data=self.get_serializer(self.get_object()).data)

    @action(['put'], True, 'shipping-address')
    def update_shipping_address(self, request, id):
        serializer = self.get_serializer(data=request.data, context={'order': self.get_object()})
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        serializer.save()

        return get_response(data={'id': id})

    # todo 발주확인 관련


class OrderItemViewSet(GenericViewSet):
    permission_classes = [OrderItemPermission]
    serializer_class = OrderItemWriteSerializer
    # queryset = OrderItem
    lookup_field = 'id'
 
    def get_queryset(self):
        if hasattr(self.request.user, 'shopper'):
            condition = Q(shopper=self.request.user.shopper)
        else:
            raise APIException('Unrecognized user.')

        return OrderItem.objects.select_related('order', 'option__product_color').filter(condition)

    def partial_update(self, request, id):
        serializer = self.get_serializer(self.get_object(), request.data, partial=True)
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        serializer.save()

        return get_response(data={'id': id})

    @action(['post'], True)
    def cancel(self, request, id):
        pass


    # @action(['put'], True, 'options')
    # def update_option(self, request, order_id, id):
    #     serializer = self.get_serializer(data=request, partial=True)

