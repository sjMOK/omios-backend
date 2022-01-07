from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from . import models, serializers
from common.utils import get_result_message, querydict_to_dict


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_categories(request):
    queryset = models.Category.objects.all()
    serializer = serializers.CategorySerializer(queryset, many=True)
    return Response(get_result_message(data=serializer.data))


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_category_info(request, pk=None):
    category = get_object_or_404(models.Category, pk=pk)
    serializer = serializers.SubCategorySerializer(category.subcategory_set.all(), many=True)
    data = {
        'name': category.name,
        'subcategory': serializer.data
    }
    return Response(get_result_message(data=data))


class ProductViewSet(viewsets.GenericViewSet):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = serializers.ProductSerializer
    lookup_field = 'pk'
    lookup_value_regex = r'[0-9]+'
    default_ordering = 'id'

    def get_queryset(self):
        queryset = serializers.Product.objects.all()
        query_params = querydict_to_dict(self.request.query_params)

        filterset = {}
        filter_mapping = {
            'category_id': 'subcategory__category_id',
            'code': 'code', 
            'subcategory_id': 'subcategory_id',
            'minprice': 'price__gte',
            'maxprice': 'price__lte',
        }

        for key, value in query_params.items():
            if key in filter_mapping:
                if isinstance(value, list):
                    filterset[filter_mapping[key] + '__in'] = value    
                else:
                    filterset[filter_mapping[key]] = value
        
        queryset = queryset.filter(**filterset)

        return queryset

    def order_queryset(self, queryset, order):
        order_mapping = {
            'popular': 'popular', 
            'created': '-created',
            'price_asc': 'price',
            'price_dsc': '-price'
        }

        if order in order_mapping.keys():
            queryset = queryset.order_by(order_mapping[order], self.default_ordering)
        else:
            queryset = queryset.order_by(self.default_ordering)

        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        
        order = request.query_params.get('order')
        if order:
            queryset = self.order_queryset(queryset, order)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)

        return Response(get_result_message(data=serializer.data))

    def create(self, request):
        return Response('product.create()')

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(get_result_message(data=serializer.data))

    def partial_update(self, request, pk=None):
        return Response('product.partial_update()')

    def destroy(self, request, pk=None):
        return Response('product.destroy()')

    @action(detail=False, methods=['GET'])
    def extra_action(self, request, pk=None):
        return Response('product.extra_actions()')

    @action(detail=True, methods=['GET'])
    def extra_action(self, request, pk=None):
        return Response('product.extra_actions_detail()')
