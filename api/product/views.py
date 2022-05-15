from django.db import connection, transaction
from django.db.models.query import Prefetch
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.mixins import ListModelMixin

from common.utils import get_response, querydict_to_dict, levenshtein, check_id_format
from common.views import upload_image_view
from user.models import ProductLike
from .models import (
    Flexibility, MainCategory, SeeThrough, SubCategory, Color, Material, LaundryInformation, 
    Style, Keyword, Product, Tag, Age, Thickness, Theme, ProductQuestionAnswer, ProductQuestionAnswerClassification,
)
from .serializers import (
    ProductReadSerializer, ProductWriteSerializer, MainCategorySerializer, SubCategorySerializer,
    AgeSerializer, StyleSerializer, MaterialSerializer, SizeSerializer, LaundryInformationSerializer,
    ColorSerializer, TagSerializer, ThicknessSerializer, SeeThroughSerializer, FlexibilitySerializer,
    ThemeSerializer, ProductQuestionAnswerSerializer, ProductQuestionAnswerClassificationSerializer,
)
from .permissions import ProductPermission, ProductQuestionAnswerPermission


def sort_keywords_by_levenshtein_distance(keywords, search_word):
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
def get_all_categories(request):
    main_categories = MainCategory.objects.prefetch_related(Prefetch('sub_categories')).all()
    serializer = MainCategorySerializer(main_categories, many=True)

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_main_categories(request):
    queryset = MainCategory.objects.all()
    serializer = MainCategorySerializer(queryset, many=True, exclude_fields=('sub_categories',))

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sub_categories_by_main_category(request, id=None):
    main_category = get_object_or_404(MainCategory, id=id)
    serializer = SubCategorySerializer(main_category.sub_categories.all(), many=True)

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_colors(request):
    queryset = Color.objects.all()
    serializer = ColorSerializer(queryset, many=True)

    return get_response(data=serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_tag_search_result(request):
    lmiting = 8
    search_word = request.query_params.get('search_word', None)

    if search_word == '' or search_word is None:
        return get_response(status=HTTP_400_BAD_REQUEST, message='Unable to search with empty string.')

    tags = Tag.objects.filter(name__contains=search_word).alias(cnt=Count('product')).order_by('-cnt')[:lmiting]
    serializer = TagSerializer(tags, many=True)

    return get_response(data=serializer.data)


@api_view(['POST'])
def upload_product_image(request):
    return upload_image_view(request, 'product', request.user.id)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_related_search_words(request):
    search_word = request.query_params.get('search_word', None)

    if search_word == '' or search_word is None:
        return get_response(status=HTTP_400_BAD_REQUEST, message='Unable to search with empty string.')

    condition = Q(name__contains=search_word)

    main_categories = MainCategory.objects.filter(condition)
    main_category_serializer = MainCategorySerializer(main_categories, many=True, exclude_fields=('sub_categories',))

    sub_categories = SubCategory.objects.filter(condition)
    sub_category_serializer = SubCategorySerializer(sub_categories, many=True)

    keywords = list(Keyword.objects.filter(condition).values_list('name', flat=True))
    sorted_keywords = sort_keywords_by_levenshtein_distance(keywords, search_word)

    response_data = {
        'main_category': main_category_serializer.data,
        'sub_category': sub_category_serializer.data,
        'keyword': sorted_keywords
    }

    return get_response(data=response_data)


def get_common_registry_data():
    response_data = {
        'color': ColorSerializer(Color.objects.all(), many=True).data,
        'material': MaterialSerializer(Material.objects.all(), many=True).data,
        'style': StyleSerializer(Style.objects.all(), many=True).data,
        'age': AgeSerializer(Age.objects.all(), many=True).data,
        'theme': ThemeSerializer(Theme.objects.all(), many=True).data,
    }

    return response_data


def get_dynamic_registry_data(sub_category_id):
    sub_category = get_object_or_404(SubCategory, id=sub_category_id)
    sizes = sub_category.sizes.all()

    response_data = {}
    response_data['size'] = SizeSerializer(sizes, many=True).data

    if sub_category.require_product_additional_information:
        thickness = Thickness.objects.all()
        see_through = SeeThrough.objects.all()
        flexibility = Flexibility.objects.all()

        response_data['thickness'] = ThicknessSerializer(thickness, many=True).data
        response_data['see_through'] = SeeThroughSerializer(see_through, many=True).data
        response_data['flexibility'] = FlexibilitySerializer(flexibility, many=True).data
        response_data['lining'] = [
            {'name': '있음', 'value': True}, 
            {'name': '없음', 'value': False},
        ]
    else:
        response_data['thickness'] = []
        response_data['see_through'] = []
        response_data['flexibility'] = []
        response_data['lining'] = []

    if sub_category.require_laundry_information:
        laundry_information = LaundryInformation.objects.all()
        response_data['laundry_information'] = LaundryInformationSerializer(laundry_information, many=True).data
    else:
        response_data['laundry_information'] = []

    return response_data


@api_view(['GET'])
@permission_classes([AllowAny])
def get_registry_data(request):
    sub_category_id = request.query_params.get('sub_category', None)

    if sub_category_id is None:
        return get_response(data=get_common_registry_data())

    if not check_id_format(sub_category_id):
        return get_response(status=HTTP_400_BAD_REQUEST, message='Query parameter sub_category must be id format.')

    return get_response(data=get_dynamic_registry_data(sub_category_id))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_question_answer_classification(request):
    queryset = ProductQuestionAnswerClassification.objects.all()
    return get_response(data=ProductQuestionAnswerClassificationSerializer(queryset, many=True).data)


class ProductViewSet(GenericViewSet):
    permission_classes = [ProductPermission]
    lookup_field = 'id'
    lookup_value_regex = r'[0-9]+'
    __default_sorting = '-created_at'
    __default_fields = ('id', 'created_at', 'name', 'price', 'sale_price', 'base_discount_rate', 'base_discounted_price')
    __read_action = ('retrieve', 'list')
    __require_write_serializer_action = ('create', 'partial_update')


    def get_serializer_class(self):
        if self.action in self.__require_write_serializer_action:
            return ProductWriteSerializer
        return ProductReadSerializer

    def __get_allow_fields(self):
        if self.detail:
            return '__all__'
        else:
            return self.__default_fields

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

        if self.action in self.__read_action:
            prefetch_images = Prefetch('images', to_attr='related_images')
            return Product.objects.prefetch_related(prefetch_images).filter(condition)
        return Product.objects.filter(condition)

    def filter_queryset(self, queryset):
        query_params = querydict_to_dict(self.request.query_params)

        filter_set = {}
        filter_mapping = {
            'min_price': 'sale_price__gte',
            'max_price': 'sale_price__lte',
            'color': 'colors__color_id',
        }

        for key, value in query_params.items():
            if key in filter_mapping:
                if isinstance(value, list):
                    filter_set[filter_mapping[key] + '__in'] = value    
                else:
                    filter_set[filter_mapping[key]] = value

        return queryset.filter(**filter_set)

    def sort_queryset(self, queryset):
        sort_mapping = {
            'price_asc': 'sale_price',
            'price_desc': '-sale_price',
        }
        sort_set = [self.__default_sorting]
        sort_key = self.request.query_params.get('sort', None)

        if sort_key is not None and sort_key in sort_mapping:
            sort_set.insert(0, sort_mapping[sort_key])

        return queryset.order_by(*sort_set)

    def __get_shoppers_like_products_id_list(self):
        shopper = self.request.user.shopper
        like_products_id_list = list(shopper.like_products.all().values_list('id', flat=True))

        return like_products_id_list

    def __get_response_for_list(self, queryset, **extra_data):
        allow_fields = self.__get_allow_fields()

        context = {'detail': self.detail, 'field_order': allow_fields}
        if hasattr(self.request.user, 'shopper'):
            context['shoppers_like_products_id_list'] = self.__get_shoppers_like_products_id_list()

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            page, allow_fields=allow_fields, many=True, context=context
        )

        paginated_response = self.get_paginated_response(serializer.data)
        paginated_response.data.update(extra_data)

        return get_response(data=paginated_response.data)

    def __get_queryset_after_search(self, queryset, search_word):
        tag_id_list = list(Tag.objects.filter(name__contains=search_word).values_list('id', flat=True))
        condition = Q(tags__id__in=tag_id_list) | Q(name__contains=search_word)

        queryset = queryset.filter(condition)

        return queryset

    def __initial_filtering(self, queryset, search_word=None, main_category=None, sub_category=None, **kwargs):
        if search_word is not None:
            queryset = self.__get_queryset_after_search(queryset, search_word)
        if main_category is not None:
            queryset = queryset.filter(sub_category__main_category_id=main_category)
        if sub_category is not None:
            queryset = queryset.filter(sub_category_id=sub_category)

        return queryset

    def list(self, request):
        queryset = self.get_queryset()

        if request.query_params.get('like_products') == 'True':
            if request.auth is not None and hasattr(request.user, 'shopper'):
                queryset = queryset.filter(like_shoppers=request.user.shopper)

        if 'search_word' in request.query_params and not request.query_params['search_word']:
            return get_response(status=HTTP_400_BAD_REQUEST, message='Unable to search with empty string.')

        if 'main_category' in request.query_params and 'sub_category' in request.query_params:
            return get_response(status=HTTP_400_BAD_REQUEST, message='You cannot filter main_category and sub_category at once.')

        queryset = self.__initial_filtering(queryset, **request.query_params.dict())
        max_price = queryset.aggregate(max_price=Max('sale_price'))['max_price']

        queryset = self.sort_queryset(
            self.filter_queryset(queryset)
        ).alias(Count('id')).only(*self.__default_fields)

        return self.__get_response_for_list(queryset, max_price=max_price)

    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data, context={'wholesaler': request.user.wholesaler})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': product.id})

    def retrieve(self, request, id=None):
        queryset = self.get_queryset().select_related(
            'sub_category__main_category', 'style', 'age', 'thickness', 'see_through', 'flexibility'
        ).annotate(total_like=Count('like_shoppers'))
        product = self.get_object(queryset)

        allow_fields = self.__get_allow_fields()
        context = {'detail': self.detail, 'field_order': self.__get_allow_fields()}

        if hasattr(request.user, 'shopper'):
            like = ProductLike.objects.filter(shopper=request.user.shopper, product=product).exists()
            context['shopper_like'] = like

        serializer = self.get_serializer(
            product, allow_fields=allow_fields, context=context
        )

        return get_response(data=serializer.data)

    @transaction.atomic
    def partial_update(self, request, id=None):
        product = self.get_object(self.get_queryset())
        serializer = ProductWriteSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return get_response(data={'id': product.id})

    @transaction.atomic
    def destroy(self, request, id=None):
        product = self.get_object(self.get_queryset())
        product.delete()

        return get_response(data={'id': product.id})


class ProductQuestionAnswerViewSet(ListModelMixin, GenericViewSet):
    permission_classes = [ProductQuestionAnswerPermission]
    lookup_field = 'id'
    lookup_url_kwarg = 'question_answer_id'
    lookup_value_regex = r'[0-9]+'
    serializer_class = ProductQuestionAnswerSerializer

    def get_queryset(self):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        queryset = ProductQuestionAnswer.objects.filter(product=product)

        if self.action == 'list':
            queryset = self.__filter_queryset(queryset).select_related('shopper', 'classification')

        return queryset

    def __filter_queryset(self, queryset):
        if 'open_qa' in self.request.query_params:
            return queryset.filter(is_secret=False)

        return queryset

    def list(self, request, product_id):
        response = super().list(request, product_id)
        return get_response(data=response.data)


    @transaction.atomic
    def create(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question_answer = serializer.save(product=product, shopper=request.user.shopper)

        return get_response(status=HTTP_201_CREATED, data={'id': question_answer.id})

    @transaction.atomic
    def partial_update(self, request, product_id, question_answer_id):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_answer = serializer.save()

        return get_response(data={'id': question_answer.id})

    @transaction.atomic
    def destroy(self, request, product_id, question_answer_id):
        question_answer = self.get_object()
        question_answer.delete()

        return get_response(data={'id': int(question_answer_id)})
