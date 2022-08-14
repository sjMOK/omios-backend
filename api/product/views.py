from django.db import connection, transaction
from django.db.models.query import Prefetch
from django.db.models import Q, Case, When, Count, Max
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.mixins import ListModelMixin

from common.utils import get_response, querydict_to_dict, levenshtein, check_integer_format
from common.views import upload_image_view
from common.permissions import IsAuthenticatedWholesaler
from common.models import SettingGroup
from coupon.models import Coupon
from user.models import is_shopper, is_wholesaler, ProductLike
from .models import MainCategory, SubCategory, Color, Keyword, Product, Tag, ProductQuestionAnswer, ProductQuestionAnswerClassification
from .serializers import (
    ProductReadSerializer, ProductRegistrationSerializer, ProductWriteSerializer, MainCategorySerializer, SubCategorySerializer, 
    ColorSerializer, TagSerializer, ProductQuestionAnswerSerializer, ProductQuestionAnswerClassificationSerializer,
)
from .permissions import ProductPermission, ProductQuestionAnswerPermission
from .paginations import ProductQuestionAnswerPagination


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

    if not search_word:
        return get_response(status=HTTP_400_BAD_REQUEST, message='Unable to search with empty string.')

    tags = Tag.objects.filter(name__contains=search_word).alias(cnt=Count('product')).order_by('-cnt')[:lmiting]
    serializer = TagSerializer(tags, many=True)

    return get_response(data=serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticatedWholesaler])
def upload_product_image(request):
    return upload_image_view(request, 'product', request.user.id)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_related_search_words(request):
    search_word = request.query_params.get('search_word', None)

    if not search_word:
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


@api_view(['GET'])
@permission_classes([IsAuthenticatedWholesaler])
def get_product_registration_data(request):
    instances = {
        'main_categories': MainCategory.objects.prefetch_related('sub_categories').all(),
        'colors': Color.objects.all(),
        'setting_groups': SettingGroup.objects.prefetch_related('items').filter(app='product')
    }

    return get_response(data=ProductRegistrationSerializer(instances).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_question_answer_classification(request):
    queryset = ProductQuestionAnswerClassification.objects.all()
    return get_response(data=ProductQuestionAnswerClassificationSerializer(queryset, many=True).data)


class ProductViewSet(GenericViewSet):
    permission_classes = [ProductPermission]
    lookup_field = 'id'
    lookup_value_regex = r'[0-9]+'
    __integer_format_validation_keys = ['main_category', 'sub_category', 'color', 'id', 'min_price', 'max_price', 'coupon']
    __filter_mapping = {
            'min_price': 'sale_price__gte',
            'max_price': 'sale_price__lte',
            'color': 'colors__color_id',
        }
    __sort_mapping = {
            'price_asc': 'sale_price',
            'price_desc': '-sale_price',
        }
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
        queryset = Product.objects.all()

        if self.request.user.is_anonymous or is_shopper(self.request.user):
            queryset = queryset.filter(on_sale=True)
        elif is_wholesaler(self.request.user) and self.action == 'list':
            queryset = queryset.filter(wholesaler=self.request.user)

        if self.action in self.__read_action:
            prefetch_images = Prefetch('images', to_attr='related_images')
            queryset = queryset.prefetch_related(prefetch_images)

            if self.action == 'retrieve':
                queryset = queryset.select_related(
                    'sub_category__main_category', 'style', 'age', 
                    'additional_information__thickness', 'additional_information__see_through',
                    'additional_information__flexibility', 'additional_information__lining',
                ).annotate(total_like=Count('like_shoppers'))
            
        return queryset

    def filter_queryset(self, queryset):
        queryset = self.__initial_filtering(queryset, **self.request.query_params.dict())
        query_params = querydict_to_dict(self.request.query_params)

        filter_set = {}
        for key, value in query_params.items():
            if key in self.__filter_mapping:
                if isinstance(value, list):
                    filter_set[self.__filter_mapping[key] + '__in'] = value    
                else:
                    filter_set[self.__filter_mapping[key]] = value

        queryset = queryset.filter(**filter_set)

        if 'coupon' in self.request.query_params:
            queryset = self.__filter_queryset_by_coupon_id(queryset, self.request.query_params['coupon'])

        return queryset.filter(**filter_set)

    def __sort_queryset(self, queryset):
        sort_set = [self.__default_sorting]
        sort_key = self.request.query_params.get('sort', None)

        if sort_key is not None and sort_key in self.__sort_mapping:
            sort_set.insert(0, self.__sort_mapping[sort_key])

        return queryset.order_by(*sort_set)

    def __get_shoppers_like_products_id_list(self):
        shopper = self.request.user.shopper
        like_products_id_list = list(shopper.like_products.all().values_list('id', flat=True))

        return like_products_id_list

    def __get_response_for_list(self, queryset, **extra_data):
        allow_fields = self.__get_allow_fields()

        context = {'detail': self.detail, 'field_order': allow_fields}
        if is_shopper(self.request.user):
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

    def __get_max_price(self):
        queryset = self.__initial_filtering(self.get_queryset(), **self.request.query_params.dict())
        max_price = queryset.aggregate(max_price=Max('sale_price'))['max_price']

        return max_price

    def __validate_query_params(self):
        for key in self.__integer_format_validation_keys:
            if key in self.request.query_params and not check_integer_format(self.request.query_params.getlist(key)):
                return get_response(status=HTTP_400_BAD_REQUEST, message='Query parameter {} must be integer format.'.format(key))

        if 'id' in self.request.query_params and len(self.request.query_params.getlist('id')) > 30:
            return get_response(status=HTTP_400_BAD_REQUEST, message='The number of id must not be more than 30.')

        if 'search_word' in self.request.query_params and not self.request.query_params['search_word']:
            return get_response(status=HTTP_400_BAD_REQUEST, message='Unable to search with empty string.')

        if 'main_category' in self.request.query_params and 'sub_category' in self.request.query_params:
            return get_response(status=HTTP_400_BAD_REQUEST, message='You cannot filter main_category and sub_category at once.')

        return

    def __filter_queryset_by_coupon_id(self, queryset, coupon_id):
        coupon = get_object_or_404(Coupon, id=coupon_id)

        if coupon.classification_id in [1, 5]:
            pass
        elif coupon.classification_id == 2:
            queryset = queryset.filter(coupon=coupon)
        elif coupon.classification_id == 3:
            sub_categories = coupon.sub_categories.all()
            queryset = queryset.filter(sub_category__in=sub_categories)
        elif coupon.classification_id ==4:
            pass

        return queryset


    def list(self, request):
        validation_exception = self.__validate_query_params()
        if validation_exception is not None:
            return validation_exception

        if 'like' in request.query_params:
            if is_shopper(request.user):
                queryset = self.get_queryset().filter(like_shoppers=request.user.shopper).order_by('-productlike__created_at')
                return self.__get_response_for_list(queryset)

        if 'id' in request.query_params:
            id_list = request.query_params.getlist('id')
            order_condition = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(id_list)])
            queryset= self.get_queryset().filter(id__in=id_list).order_by(order_condition)
            return self.__get_response_for_list(queryset)

        queryset = self.__sort_queryset(
            self.filter_queryset(
                self.get_queryset()
            ).alias(Count('id'))
        )

        return self.__get_response_for_list(queryset, max_price=self.__get_max_price())

    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data, context={'wholesaler': request.user.wholesaler})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        return get_response(status=HTTP_201_CREATED, data={'id': product.id})

    def retrieve(self, request, id=None):
        product = self.get_object(self.get_queryset())
        allow_fields = self.__get_allow_fields()
        context = {'detail': self.detail, 'field_order': self.__get_allow_fields()}

        if is_shopper(request.user):
            shopper_like = ProductLike.objects.filter(shopper=request.user.shopper, product=product).exists()
            context['shopper_like'] = shopper_like

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
    pagination_class = ProductQuestionAnswerPagination

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
