from django.db import transaction

from rest_framework.serializers import (
    Serializer, CharField, ListField, BooleanField, IntegerField, URLField, ChoiceField, DateTimeField,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.openapi import Parameter, IN_QUERY, TYPE_STRING

from common.documentations import Image, get_response
from .serializers import (
    SubCategorySerializer, MainCategorySerializer, SizeSerializer, LaundryInformationSerializer, ThicknessSerializer,
    SeeThroughSerializer, FlexibilitySerializer, AgeSerializer, ThemeSerializer, ColorSerializer, StyleSerializer,
    MaterialSerializer, TagSerializer, ProductImageSerializer, ProductMaterialSerializer, OptionSerializer, 
    ProductColorSerializer, ProductReadSerializer, ProductWriteSerializer, ProductQuestionAnswerSerializer,
    ProductQuestionAnswerClassificationSerializer,
)
from .views import (
    ProductViewSet, ProductQuestionAnswerViewSet,
    get_all_categories, get_main_categories, get_sub_categories_by_main_category, get_colors, get_tag_search_result, 
    upload_product_image, get_related_search_words, get_registry_data, get_product_question_answer_classification,
)


get_registry_data_view_operation_description = '''상품 등록시 필요한 데이터 가져오기
sub_category 쿼리스트링을 넘기지 않을 경우 공통 데이터("color", "material", "style", "age", "theme")를 반환
sub_category 쿼리스트링을 넘길 경우 동적 데이터("size", "thickness", "see_through", "flexibility", "lining", "laundry_information")를 반환
동적 데이터는 sub_category에 따라 각 데이터(배열)의 길이가 달라지며 빈 배열일 수 있음
'''


class RegistryDynamicQuerySerializer(Serializer):
    sub_category = IntegerField()


class SearchQuerySerializer(Serializer):
    search_word = CharField(min_length=1, help_text='검색어, 1글자 이상')


class ProductListQuerySerializer(Serializer):
    search_word = CharField(min_length=1, required=False, help_text='검색어')
    main_category = IntegerField(required=False, help_text='메인 카테고리 필터링 - id 값')
    sub_category = IntegerField(required=False, help_text='서브 카테고리 필터링 - id 값')
    min_price = IntegerField(required=False, help_text='최소 가격 필터링')
    max_price = IntegerField(required=False, help_text='최대 가격 필터링')
    color = ListField(child=IntegerField(), required=False, help_text='색상 필터링 - id 값, 다중 값 가능(배열)')
    sort = ChoiceField(
        choices=['price_asc', 'price_desc'],
        required=False,
        help_text='price_asc: 가격 오름차순\nprice_desc: 가격 내림차순'
    )


class ProductCreateRequest(ProductWriteSerializer):
    class ProductMaterialCreateRequest(ProductMaterialSerializer):
        id = None  


    class ProductImageCreateRequest(ProductImageSerializer):
        id = None


    class OptionCreateRequest(OptionSerializer):
        id = None


    class ProductColorCreateRequest(ProductColorSerializer):
        id = None


    options = OptionCreateRequest()
    images = ProductImageCreateRequest()
    materials = ProductMaterialCreateRequest()
    colors = ProductColorCreateRequest()


class MainCategoryResponse(MainCategorySerializer):
    sub_categories = None


class SearchBoxResponse(Serializer):
    main_category = MainCategoryResponse(many=True)
    sub_category = SubCategorySerializer(many=True)
    keyword = ListField(child=CharField())


class RegistryCommonResponse(Serializer):
    color = ColorSerializer(many=True)
    material = MaterialSerializer(many=True)
    style = StyleSerializer(many=True)
    age = AgeSerializer(many=True)
    theme = ThemeSerializer(many=True)


class RegistryDynamicResponse(Serializer):
    class LinigResponse(Serializer):
        name = CharField()
        value = BooleanField()

    size = SizeSerializer(many=True)
    thickness = ThicknessSerializer(many=True, allow_empty=True)
    see_through = SeeThroughSerializer(many=True, allow_empty=True)
    flexibility = FlexibilitySerializer(many=True, allow_empty=True)
    lining = LinigResponse(many=True, allow_empty=True)
    laundry_information = LaundryInformationSerializer(many=True, allow_empty=True)


class RegistryDataResponse(Serializer):
    class LinigResponse(Serializer):
        name = CharField()
        value = BooleanField()

    color = ColorSerializer(many=True, required=False)
    material = MaterialSerializer(many=True, required=False)
    style = StyleSerializer(many=True, required=False)
    age = AgeSerializer(many=True, required=False)
    theme = ThemeSerializer(many=True, required=False)
    size = SizeSerializer(many=True, required=False)
    thickness = ThicknessSerializer(many=True, required=False, allow_empty=True)
    see_through = SeeThroughSerializer(many=True, required=False, allow_empty=True)
    flexibility = FlexibilitySerializer(many=True, required=False, allow_empty=True)
    lining = LinigResponse(many=True, required=False, allow_empty=True)
    laundry_information = LaundryInformationSerializer(many=True, required=False, allow_empty=True)


class ProductListResponse(Serializer):
    class ResultsResponse(Serializer):
        id = IntegerField()
        created_at = DateTimeField()
        name = CharField()
        price = IntegerField
        sale_price = IntegerField()
        base_discount_rate = IntegerField()
        base_discounted_price = IntegerField()
        main_image = URLField()
        shopper_like = BooleanField()

    count = IntegerField()
    next = URLField(allow_null=True)
    previous = URLField(allow_null=True)
    results = ResultsResponse()
    max_price = IntegerField()


class ProductDetailResponse(ProductReadSerializer):
    main_category = MainCategoryResponse()
    shopper_like = BooleanField()


class ProductQuestionAnswerResponse(ProductQuestionAnswerSerializer):
    classification = CharField()


class DecoratedProductViewSet(ProductViewSet):
    shopper_token_discription = '\nShopper app의 경우 토큰이 필수 값 아님(anonymous user 가능)'
    list_description = '''상품 정보 리스트 조회
    \npage를 직접 query parameter로 전달해 원하는 페이지의 리스트를 가져올 수 있음
    \n여러 필터를 동시에 적용 가능
    * 메인 카테고리와 서브 카테고리는 동시에 필터링 할 수 없으며 여러개의 키 값을 전달할 수 없음*
    \n기본적으로 등록 시간 내림차순(최근 순)으로 정렬되어 있음
    '''
    partial_update_description = '''
    상품 Id로 상품 수정

    신규 생성 데이터는 등록 시와 같은 포맷
    예) "materials": {
        "material": "가죽",
        "mixing_rate": 100
    }

    수정 데이터는 딕셔너리에 id 포함
    예) "materials": {
        "id": 100,
        "material": 가죽,
        "mixing_rate": 100
    }

    삭제 데이터는 딕셔너리에 id만
    예) "materials": {
        "id": 100
    }

    "materials"와 "images"는 수정 시 수정을 가하지 않는 데이터도 모두 body에 담아야 함.(PUT 형식)
    '''

    @swagger_auto_schema(query_serializer=ProductListQuerySerializer, **get_response(ProductListResponse()), operation_description=list_description + shopper_token_discription)
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(**get_response(ProductDetailResponse()), operation_description='상품 Id로 상품 정보 조회\n'+ shopper_token_discription)
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @swagger_auto_schema(request_body=ProductCreateRequest(), **get_response(code=201), operation_description='상품 등록')
    @transaction.atomic
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(request_body=ProductWriteSerializer(), **get_response(), operation_description=partial_update_description)
    @transaction.atomic
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_auto_schema(**get_response(), operation_description='상품 Id로 상품 삭제')
    @transaction.atomic
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)


class DecoratedProductQuestionAnswerViewSet(ProductQuestionAnswerViewSet):
    list_description = '''
    Q&A 리스트 조회
    비밀 글 제외 시 "open_qa" 키를 query parameter로 넘김(value 없이 key만)
    '''

    @swagger_auto_schema(manual_parameters=[Parameter('open_qa', IN_QUERY, type=TYPE_STRING, description='비밀 글 제외')], security=[], **get_response(ProductQuestionAnswerResponse(many=True)), operation_description=list_description)
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @swagger_auto_schema(request_body=ProductQuestionAnswerSerializer(), **get_response(code=201), operation_description='Q&A 등록')
    @transaction.atomic
    def create(self, *args, **kwargs):
        return super().create(*args, **kwargs)

    @swagger_auto_schema(request_body=ProductQuestionAnswerSerializer(), **get_response(), operation_description='Q&A 수정')
    @transaction.atomic
    def partial_update(self, *args, **kwargs):
        return super().partial_update(*args, **kwargs)

    @swagger_auto_schema(**get_response(), operation_description='Q&A 삭제')
    @transaction.atomic
    def destroy(self, *args, **kwargs):
        return super().destroy(*args, **kwargs)


decorated_get_all_categories_view = swagger_auto_schema(
    method='GET', **get_response(MainCategorySerializer(many=True)), security=[], operation_description='모든 메인 카테고리와 서브 카테고리 가져오기'
)(get_all_categories)

decorated_get_main_categories_view = swagger_auto_schema(
    method='GET', **get_response(MainCategoryResponse(many=True)), security=[], operation_description='메인 카테고리 가져오기'
)(get_main_categories)

decorated_sub_category_view = swagger_auto_schema(
    method='GET', **get_response(SubCategorySerializer()), security=[], operation_description='특정 메인 카테고리 Id에 해당하는 서브 카테고리 가져오기'
)(get_sub_categories_by_main_category)

decorated_get_colors_view = swagger_auto_schema(
    method='GET', **get_response(ColorSerializer(many=True)), security=[], operation_description='상품 색상 가져오기'
)(get_colors)

decorated_get_tag_search_result_view = swagger_auto_schema(
    method='GET', query_serializer=SearchQuerySerializer, **get_response(TagSerializer(many=True)), security=[], operation_description='검색어(문자열)로 상품 태그 검색\nquery 필수 빈 문자열 허용하지 않음'
)(get_tag_search_result)

decorated_upload_product_image_view = swagger_auto_schema(
    method='POST', request_body=Image, **get_response(Image(), 201), operation_description='상품 이미지 업로드\n요청 시에는 파일 전체를 보내야 함\n응답 시에는 저장된 url을 반환'
)(upload_product_image)

decorated_get_related_search_words_view = swagger_auto_schema(
    method='GET', query_serializer=SearchQuerySerializer, **get_response(SearchBoxResponse()), security=[], operation_description='검색어(문자열)와 유사한 메인 카테고리, 서브 카테고리, 키워드 데이터 GET\nquery 필수, 빈 문자열 허용하지 않음.'
)(get_related_search_words)

decorated_get_registry_data_view = swagger_auto_schema(
    method='GET', **get_response(RegistryDataResponse()), security=[], operation_description=get_registry_data_view_operation_description
)(get_registry_data)

decorated_get_product_question_answer_classification = swagger_auto_schema(
    method='GET', **get_response(ProductQuestionAnswerClassificationSerializer(many=True)), security=[], operation_description='상품 Q&A 분류 리스트 조회'
)(get_product_question_answer_classification)
