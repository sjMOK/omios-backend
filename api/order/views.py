from django.db.models import Count
from django.db.models.query import Prefetch
from django.db.transaction import atomic

from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from common.utils import get_response
from common.permissions import IsEasyAdminUser
from user.models import Shopper
from product.models import ProductImage
from .models import (
    PAYMENT_COMPLETION_STATUS, NORMAL_STATUS,
    Order, OrderItem, Status, StatusHistory
)
from .serializers import (
    OrderSerializer, OrderWriteSerializer, OrderItemWriteSerializer, OrderItemStatisticsSerializer, ShippingAddressSerializer, 
    CancellationInformationSerializer, StatusHistorySerializer, OrderConfirmSerializer, DeliverySerializer
)
from .paginations import OrderPagination
from .permissions import OrderPermission, OrderItemPermission


class OrderViewSet(GenericViewSet):
    pagination_class = OrderPagination
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

    def __apply_filters(self, order_queryset, item_queryset):
        if self.action != 'list':
            return order_queryset, item_queryset

        if 'status' in self.request.query_params:
            status = Status.objects.filter(name=self.request.query_params['status']).first()
            order_queryset = order_queryset.filter(items__status=status).annotate(count=Count('id')).order_by('-id')
            item_queryset = item_queryset.filter(status=status)
        
        if 'start_date' in self.request.query_params and 'end_date' in self.request.query_params:
            order_queryset = order_queryset.filter(created_at__range=[
                self.request.query_params['start_date'], 
                self.request.query_params['end_date'] + ' 23:59:59',
            ])

        return order_queryset.filter(shopper_id=self.request.user.id), item_queryset

    def get_queryset(self):
        queryset = Order.objects

        if self.action in ['list', 'retrieve']:
            images = ProductImage.objects.filter(sequence=1)
            item_queryset = OrderItem.objects.select_related('option__product_color__product', 'status'). \
                prefetch_related(Prefetch('option__product_color__product__images', images))

            queryset, item_queryset = self.__apply_filters(queryset, item_queryset)
            queryset = queryset.select_related('shipping_address').prefetch_related(Prefetch('items', item_queryset))

        return queryset

    def list(self, request):
        serializer = self.get_serializer(self.paginate_queryset(self.get_queryset()), many=True)

        return get_response(data=self.get_paginated_response(serializer.data).data)

    @atomic
    def create(self, request):
        shopper = Shopper.objects.select_related('membership').get(user=request.user)
        serializer = self.get_serializer(data=request.data, context={'shopper': shopper})

        serializer.is_valid(raise_exception=True)

        # todo
        # 결제 로직 + 결제 관련 상태 (입금 대기 or 결제 완료)

        order = serializer.save(status_id=PAYMENT_COMPLETION_STATUS)

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
    @action(['post'], False, 'confirm', permission_classes=[IsEasyAdminUser])
    def confirm(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return get_response(status=HTTP_201_CREATED, data=serializer.save())

    @atomic
    @action(['post'], False, 'delivery', permission_classes=[IsEasyAdminUser])
    def delivery(self, request):
        if len(request.data) > 50:
            return get_response(status=HTTP_400_BAD_REQUEST, message='You can only request up to 50 at a time.')

        serializer = self.get_serializer(data=request.data, many=True, allow_empty=False)
        serializer.is_valid(raise_exception=True)
        
        return get_response(status=HTTP_201_CREATED, data=serializer.save())


class OrderItemViewSet(GenericViewSet):
    pagination_class = None
    permission_classes = [OrderItemPermission]
    lookup_field = 'id'
    lookup_url_kwarg = 'item_id'
    __patchable_fields = set(['option'])
 
    def get_serializer_class(self):
        if self.action == 'get_statistics':
            return OrderItemStatisticsSerializer

        return OrderItemWriteSerializer

    def get_queryset(self):
        queryset = OrderItem.objects
        if self.action == 'partial_update':
            queryset = queryset.select_related('order', 'option__product_color')
        elif self.action == 'get_statistics':
            queryset = queryset.filter(order__shopper_id=self.request.user.id, status__in=NORMAL_STATUS) \
                .values('status', 'status__name').annotate(count=Count('*')).order_by('status')

        return queryset        

    def partial_update(self, request, item_id):
        if set(request.data).difference(self.__patchable_fields):
            return get_response(status=HTTP_400_BAD_REQUEST, message='It contains requests for fields that do not exist or cannot be modified.')

        serializer = self.get_serializer(self.get_object(), request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return get_response(data={'id': int(item_id)})

    @action(['get'], False, 'statistics')
    def get_statistics(self, request):
        return get_response(data=self.get_serializer(self.get_queryset(), many=True).data)


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
