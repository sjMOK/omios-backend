from django.db import connection
from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from . import models, serializers, permissions
from common.utils import get_result_message, querydict_to_dict, base64_to_imgfile


@api_view(['GET'])
@permission_classes([AllowAny])
def get_main_categories(request):
    queryset = models.MainCategory.objects.all()
    serializer = serializers.MainCategorySerializer(queryset, many=True)

    return Response(get_result_message(data=serializer.data))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sub_categories(request, pk=None):
    main_category = get_object_or_404(models.MainCategory, pk=pk)
    serializer = serializers.SubCategorySerializer(main_category.subcategory_set.all(), many=True)
    data = {
        'main_category_id': main_category.id,
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
    allowed_fields = {
        'shopper_list': ('name', 'price'),
        'shopper_retrieve': ('id', 'name', 'code', 'created', 'price', 'sub_category', 'main_category', 'options', 'images'),
        'wholesaler_list': ('id',),
        'wholesaler_retrieve': ('name',),
    }

    def get_allowed_fields(self):
        if hasattr(self.request.user, 'wholesaler'):
            return self.allowed_fields['wholesaler_{0}'.format(self.action)]
        
        return self.allowed_fields['shopper_{0}'.format(self.action)]

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

    def list(self, request):
        queryset = self.sort_queryset(
            self.filter_queryset(self.get_queryset())
        )
        prefetch = Prefetch('images', to_attr='related_images')
        queryset = queryset.prefetch_related(prefetch)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, fields=self.get_allowed_fields(), many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response(connection.queries)
            return Response(get_result_message(data=paginated_response.data))
        
        serializer = self.get_serializer(queryset, fields=self.get_allowed_fields(), many=True)
        
        return Response(get_result_message(data=serializer.data))

    def create(self, request):
        images = request.data.get('images', None)
        for image in images:
            image['url'] = base64_to_imgfile(image['url'])
    
        serializer = self.get_serializer(data=request.data, context={'wholesaler': request.user.wholesaler})

        if not serializer.is_valid():
            return Response(get_result_message(HTTP_400_BAD_REQUEST, serializer.errors), status=HTTP_400_BAD_REQUEST)

        product = serializer.save()
        
        return Response(get_result_message(data={'id': product.id}))

    def retrieve(self, request, pk=None):
        prefetch_options = Prefetch('options', queryset=models.Option.objects.select_related('size'), to_attr='related_options')
        prefetch_images = Prefetch('images', to_attr='related_images')
        product = models.Product.objects.prefetch_related(prefetch_options, prefetch_images).select_related('sub_category__main_category').get(id=pk)
        self.check_object_permissions(request, product)
        
        serializer = self.get_serializer(product, fields=self.get_allowed_fields())
        serializer.data
        return Response(connection.queries)
        return Response(get_result_message(data=serializer.data))

    def partial_update(self, request, pk=None):
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response('product.partial_update()')

    def destroy(self, request, pk=None):
        product = self.get_object()
        product.on_sale = False
        product.save()

        return Response(get_result_message(data={'id': product.id}), status=HTTP_200_OK)
