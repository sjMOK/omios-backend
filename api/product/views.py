from django.db import connection
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from . import models, serializers, permissions
from common.utils import get_result_message, querydict_to_dict


@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories(request):
    queryset = models.MainCategory.objects.all()
    serializer = serializers.MainCategorySerializer(queryset, many=True)

    return Response(get_result_message(data=serializer.data))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sub_categories(request, pk=None):
    main_category = get_object_or_404(models.MainCategory, pk=pk)
    serializer = serializers.SubCategorySerializer(main_category.subcategory_set.all(), many=True)
    data = {
        'name': main_category.name,
        'sub_category': serializer.data,
    }

    return Response(get_result_message(data=data))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_colors(request):
    queryset = models.Color.objects.all()
    serializer = serializers.ColorSerializer(queryset, many=True)

    return Response(get_result_message(data=serializer.data))


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
            'main_category': 'sub_category__main_category_id',
            'sub_category': 'sub_category_id',
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
        return serializers.ProductSerializer

    def list(self, request):
        queryset = self.sort_queryset(
            self.filter_queryset(self.get_queryset())
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            return Response(get_result_message(data=paginated_response.data))
        
        serializer = self.get_serializer(queryset, many=True)

        return Response(get_result_message(data=serializer.data))

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(get_result_message(HTTP_400_BAD_REQUEST, serializer.errors), status=HTTP_400_BAD_REQUEST)

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
