from django.db import connection
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from . import models, serializers, permissions
from common.utils import get_result_message, querydict_to_dict


@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories(request):
    queryset = models.Category.objects.all()
    serializer = serializers.CategorySerializer(queryset, many=True)

    return Response(get_result_message(data=serializer.data))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_category_info(request, pk=None):
    category = get_object_or_404(models.Category, pk=pk)
    serializer = serializers.SubCategorySerializer(category.subcategory_set.all(), many=True)
    data = {
        'name': category.name,
        'subcategory': serializer.data,
    }

    return Response(get_result_message(data=data))


class ProductViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.ProductPermission]
    serializer_class = serializers.ProductSerializer
    lookup_field = 'pk'
    lookup_value_regex = r'[0-9]+'
    default_sorting = '-created'

    def get_queryset(self):
        queryset = models.Product.objects.all()
        if hasattr(self.request.user, 'wholesaler'):
            queryset = queryset.filter(wholesaler=self.request.user)
        
        return queryset

    def filter_queryset(self, queryset):
        query_params = querydict_to_dict(self.request.query_params)

        filterset = {}
        filter_mapping = {
            'category_id': 'subcategory__category_id',
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

    def sort_queryset(self, queryset):
        sort_mapping = {
            'popular': 'popular',
            'created': '-created',
            'price_asc': 'price',
            'price_dsc': '-price',
        }
        
        field_names = []
        sort = self.request.query_params.get('sort', None)
        if sort and sort in sort_mapping:
            field_names.append(sort_mapping[sort])
        field_names.append(self.default_sorting)

        queryset = queryset.order_by(*field_names)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.ProductListSerializer
        else:
            return serializers.ProductSerializer

    def list(self, request):
        queryset = self.sort_queryset(
            self.filter_queryset(self.get_queryset())
        )

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
        instance = self.get_object()
        return Response('product.partial_update()')

    def destroy(self, request, pk=None):
        instance = self.get_object()
        return Response('product.destroy()')

    @action(detail=False, methods=['GET'])
    def extra_action(self, request, pk=None):
        return Response('product.extra_actions()')

    @action(detail=True, methods=['GET'])
    def extra_action(self, request, pk=None):
        return Response('product.extra_actions_detail()')


class TestViewSet(viewsets.GenericViewSet):
    permission_classes = []
    def list(self, request):
        return Response('.list()')