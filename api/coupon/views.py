from datetime import date

from django.db.models import Q, Prefetch
from django.db import connection
from django.shortcuts import get_object_or_404

from rest_framework.viewsets import GenericViewSet
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.decorators import action

from common.permissions import IsAdminUser
from common.utils import get_response, check_integer_format
from user.models import is_shopper
from product.models import Product
from product.serializers import ProductReadSerializer
from .models import Coupon
from .serializers import CouponSerializer
from .permissions import CouponPermission


class CouponViewSet(GenericViewSet):
    permission_classes = [CouponPermission | IsAdminUser]
    serializer_class = CouponSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'coupon_id'
    lookup_value_regex = r'[0-9]+'

    def get_queryset(self):
        queryset = Coupon.objects.all()
        if self.request.user.is_authenticated and self.request.user.is_admin:
            return queryset

        end_date_condition = Q(end_date__gte=date.today()) | Q(end_date__isnull=True)
        queryset = queryset.filter(end_date_condition, is_auto_issue=False)

        product_id = self.request.query_params.get('product', None)
        if product_id is not None:
            product = get_object_or_404(Product, id=product_id)
            filter_condition = Q(products=product) | Q(sub_categories=product.sub_category_id)
            queryset = queryset.filter(filter_condition)

        return queryset

    def list(self, request):
        product_id = self.request.query_params.get('product', None)
        if product_id is not None and not check_integer_format(product_id):
            return get_response(status=HTTP_400_BAD_REQUEST, message='Query parameter product must be id format.')

        queryset = self.get_queryset()

        context = {}
        if is_shopper(request.user):
            owned_coupon_id_list = list(request.user.shopper.coupons.all().values_list('id', flat=True))
            context['owned_coupon_id_list']= owned_coupon_id_list

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True, context=context)

        paginated_response = self.get_paginated_response(serializer.data)

        return get_response(data=paginated_response.data)

    def create(self, requset):
        serializer = self.get_serializer(data=requset.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': coupon.id})
