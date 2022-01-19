from django.db import connection
from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404
from django.http import Http404

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
def get_sub_categories(request, id=None):
    main_category = get_object_or_404(models.MainCategory, id=id)
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


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def query(request):
    names = request.data.get('names')
    for name in names:
        name = name.upper()
    # for name in names:
    #     name['name'] = name['name'].upper()

    return Response(request.data)
    return Response(connection.queries)


class ProductViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.ProductPermission]
    serializer_class = serializers.ProductSerializer
    lookup_field = 'id'
    lookup_value_regex = r'[0-9]+'
    default_sorting = '-created'
    default_fields = ('id', 'name', 'price',)
    additional_fields = {
        'shopper_list': (),
        'shopper_retrieve': ('options', 'images', 'sub_category',),
        'wholesaler_list': ('created',),
        'wholesaler_retrieve': ('options', 'code', 'sub_category', 'created', 'on_sale', 'images',),
    }

    def get_allowed_fields(self):
        user_action = 'wholesaler_{0}'.format(self.action) if hasattr(self.request.user, 'wholesaler') else 'shopper_{0}'.format(self.action)
        return self.default_fields + self.additional_fields[user_action]

    def get_object(self, queryset):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        try:
            obj = get_object_or_404(queryset, **filter_kwargs)
        except (TypeError, ValueError, ValueError):
            raise Http404

        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        if hasattr(self.request.user, 'wholesaler'):
            return models.Product.objects.filter(wholesaler=self.request.user)
        return models.Product.objects.filter(on_sale=True)

    def filter_queryset(self, queryset):
        query_params = querydict_to_dict(self.request.query_params)

        filterset = {}
        filter_mapping = {
            'main_category': 'sub_category__main_category_id',
            'sub_category': 'sub_category_id',
            'minprice': 'price__gte',
            'maxprice': 'price__lte',
            'color': 'options__color_id',
        }

        for key, value in query_params.items():
            if key in filter_mapping:
                if isinstance(value, list):
                    filterset[filter_mapping[key] + '__in'] = value    
                else:
                    filterset[filter_mapping[key]] = value
        
        return queryset.filter(**filterset).distinct()

    def sort_queryset(self, queryset):
        sort_mapping = {
            'popular': 'popular',
            'created': '-created',
            'price_asc': 'price',
            'price_dsc': '-price',
        }
        sort_set = [self.default_sorting]
        sort = self.request.query_params.get('sort', None)

        if sort and sort in sort_mapping:
            sort_set.insert(0, sort_mapping[sort])

        return queryset.order_by(*sort_set)

    def retrieve(self, request, id=None):
        prefetch_options = Prefetch('options', queryset=models.Option.objects.select_related('size'), to_attr='related_options')
        prefetch_images = Prefetch('images', to_attr='related_images')

        queryset = self.filter_queryset(
            self.get_queryset().prefetch_related(prefetch_options, prefetch_images).select_related('sub_category__main_category')
        )
    
        product = self.get_object(queryset)
        
        serializer = self.get_serializer(product, fields=self.get_allowed_fields(), context={'action': self.action, 'user': self.request.user})

        return Response(get_result_message(data=serializer.data))

    def list(self, request):
        prefetch_images = Prefetch('images', to_attr='related_images')
        queryset = self.sort_queryset(
            self.filter_queryset(
                self.get_queryset().prefetch_related(prefetch_images)
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, fields=self.get_allowed_fields(), many=True, context={'action': self.action, 'user': self.request.user}
            )
            paginated_response = self.get_paginated_response(serializer.data)
            return Response(get_result_message(data=paginated_response.data))
        
        serializer = self.get_serializer(queryset, fields=self.get_allowed_fields(), many=True)
        
        return Response(get_result_message(data=serializer.data))

    def create(self, request):
        images = request.data.get('images', list())
    
        for image in images:
            image['url'] = base64_to_imgfile(image['url'])
        
        serializer = self.get_serializer(data=request.data, context={'wholesaler': request.user.wholesaler})
        if not serializer.is_valid():
            return Response(get_result_message(HTTP_400_BAD_REQUEST, serializer.errors), status=HTTP_400_BAD_REQUEST)

        product = serializer.save()

        return Response(connection.queries)
        return Response(get_result_message(data={'id': product.id}))

    def partial_update(self, request, id=None):
        product = self.get_object(self.get_queryset())
        serializer = self.get_serializer(product, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response('product.partial_update()')

    def destroy(self, request, id=None):
        product = self.get_object(self.get_queryset())
        product.on_sale = False
        product.save()

        return Response(get_result_message(data={'id': product.id}), status=HTTP_200_OK)
