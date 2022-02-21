from django.db.models.query import Prefetch
from django.db import connection
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from . import models, serializers, permissions
from common.utils import get_response, querydict_to_dict, levenshtein
from common.storage import upload_images


def sort_keywords(keywords, search_word):
    keywords_leven_distance = [
        {'name': keyword, 'distance': levenshtein(search_word, keyword)}
        for keyword in keywords
    ]

    sorted_keywords = sorted(keywords_leven_distance, key=lambda x: (x['distance'], x['name']))
    if len(sorted_keywords) > 10:
        sorted_keywords = sorted_keywords[:10]

    return [keyword['name'] for keyword in sorted_keywords]


@api_view(['GET'])
@permission_classes([AllowAny])
def get_searchbox_data(request):
    search_word = request.query_params.get('query', None)

    if search_word is None:
        return get_response(status=HTTP_400_BAD_REQUEST, message='search word is required.')

    condition = Q(name__contains=search_word)

    main_categories = models.MainCategory.objects.filter(condition)
    main_category_serializer = serializers.MainCategorySerializer(main_categories, many=True)

    sub_categories = models.SubCategory.objects.filter(condition)
    sub_category_serializer = serializers.SubCategorySerializer(sub_categories, many=True)

    keywords = list(models.Keyword.objects.filter(condition).values_list('name', flat=True))
    sorted_keywords = sort_keywords(keywords, search_word)

    response_data = {
        'main_category': main_category_serializer.data,
        'sub_category': sub_category_serializer.data,
        'keyword': sorted_keywords
    }

    return get_response(data=response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_common_registration_data(request):
    colors = Color.objects.all()
    materials=  Material.objects.all()
    styles = Style.objects.all()
    ages = Age.objects.all()

    response_data = {}
    response_data['color'] = ColorSerializer(colors, many=True).data
    response_data['material'] = MaterialSerializer(materials, many=True).data
    response_data['style'] = StyleSerializer(styles , many=True).data
    response_data['age'] = AgeSerializer(ages, many=True).data

    return get_response(data=response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dynamic_registation_data(request):
    sub_category_id = request.query_params.get('sub_category', None)
    if sub_category_id is None:
        return get_response(status=400, message='this request should include sub_category.')

    sub_category = SubCategory.objects.get(id=sub_category_id)

    sizes = sub_category.sizes.all()

    response_data = dict()
    response_data['size'] = SizeSerializer(sizes, many=True).data

    if sub_category.require_product_additional_information:
        thickness = Thickness.objects.all()
        see_through = SeeThrough.objects.all()
        flexibility = Flexibility.objects.all()

        product_additional_inforamtion = dict()
        product_additional_inforamtion['thickness'] = ThicknessSerializer(thickness, many=True).data
        product_additional_inforamtion['see_through'] = SeeThroughSerializer(see_through, many=True).data
        product_additional_inforamtion['flexibility'] = FlexibilitySerializer(flexibility, many=True).data

        response_data['product_additional_information'] = product_additional_inforamtion

    if sub_category.require_laundry_information:
        laundry_information = LaundryInformation.objects.all()
        response_data['laundry_inforamtion'] = LaundryInformationSerializer(laundry_information, many=True).data

    return get_response(data=response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_categories(request):
    main_categories = MainCategory.objects.all()
    serializer = MainCategorySerializer(main_categories, many=True)

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_main_categories(request):
    queryset = MainCategory.objects.all()
    serializer = MainCategorySerializer(queryset, many=True, exclude_fields=('id', 'name', 'image_url'))

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sub_categories_by_main_category(request, id=None):
    main_category = get_object_or_404(MainCategory, id=id)
    serializer = SubCategorySerializer(main_category.sub_categories.all(), many=True, allow_fields=('id', 'name'))

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_colors(request):
    queryset = models.Color.objects.all()
    serializer = serializers.ColorSerializer(queryset, many=True)

    return get_response(data=serializer.data)


@api_view(['POST'])
def upload_prdocut_image(request):
    images = request.FILES.getlist('image')

    serializer = serializers.ImageSerializer(data=[{'image': image} for image in images], many=True)
    if not serializer.is_valid():
        return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

    images = upload_images('product', request.user.id, images)

    return get_response(status=HTTP_201_CREATED, data={'images': images})


class ProductViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.ProductPermission]
    serializer_class = serializers.ProductSerializer
    lookup_field = 'id'
    lookup_value_regex = r'[0-9]+'
    default_sorting = '-created'
    default_fields = ('id', 'name', 'price')
    additional_fields = {
        'shopper_list': (),
        'shopper_detail': ('options', 'sub_category', 'images', 'tags'),
        'wholesaler_list': ('created',),
        'wholesaler_detail': ('options', 'code', 'sub_category', 'created', 'on_sale', 'images', 'tags'),
    }

    def get_allowed_fields(self):
        request_type = 'detail' if self.detail else 'list'
        user_action = 'wholesaler_{0}'.format(request_type) if hasattr(self.request.user, 'wholesaler') else 'shopper_{0}'.format(request_type)

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
            condition = Q(wholesaler=self.request.user)
        else:
            condition = Q(on_sale=True)

        prefetch_images = Prefetch('images', to_attr='related_images')
        prefetch_tags = Prefetch('tags', to_attr='related_tags')

        return models.Product.objects.prefetch_related(prefetch_images, prefetch_tags).filter(condition)

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

        return queryset.filter(**filterset)                     

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

    def get_response_for_list(self, queryset, **extra_data):
        queryset = self.sort_queryset(
            self.filter_queryset(queryset)
        ).alias(Count('id')).only(*self.default_fields)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            page, fields=self.get_allowed_fields(), many=True, context={'detail': self.detail}
        )

        paginated_response = self.get_paginated_response(serializer.data)
        paginated_response.data.update(extra_data)

        return get_response(data=paginated_response.data)

    def list(self, request):
        queryset = self.get_queryset()

        if 'main_category' in request.query_params:
            queryset = queryset.filter(sub_category__main_category_id=request.query_params.get('main_category'))
        if 'sub_category' in request.query_params:
            queryset = queryset.filter(sub_category_id=request.query_params.get('sub_category'))

        max_price = queryset.aggregate(max_price=Max('price'))['max_price']

        return self.get_response_for_list(queryset, max_price=max_price)

    def retrieve(self, request, id=None):
        prefetch_options = Prefetch('options', queryset=models.Option.objects.select_related('size'), to_attr='related_options')

        queryset = self.filter_queryset(
            self.get_queryset().prefetch_related(prefetch_options).select_related('sub_category__main_category')
        )
    
        product = self.get_object(queryset)

        serializer = self.get_serializer(product, fields=self.get_allowed_fields(), context={'detail': self.detail})

        return get_response(data=serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data, context={'wholesaler': request.user.wholesaler})
        if not serializer.is_valid():
            return get_response(status=HTTP_400_BAD_REQUEST, message=serializer.errors)

        product = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': product.id})

    def partial_update(self, request, id=None):
        return get_response(data='product.partial_update()')

    def destroy(self, request, id=None):
        product = self.get_object(self.get_queryset())
        product.on_sale = False
        product.save()

        return get_response(data={'id': product.id})

    @action(detail=False, url_path='search')
    def search(self, request):
        search_word = request.query_params.get('query', None)
        if search_word is None:
            return get_response(status=HTTP_400_BAD_REQUEST, message='Unable to search with empty string.')

        tag_id_list = list(models.Tag.objects.filter(name__contains=search_word).values_list('id', flat=True))
        condition = Q(tags__id__in=tag_id_list) | Q(name__contains=search_word)

        queryset = self.get_queryset().filter(condition)
        max_price = queryset.aggregate(max_price=Max('price'))['max_price']

        return self.get_response_for_list(queryset, max_price=max_price)
