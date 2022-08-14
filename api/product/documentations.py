from django.db import transaction

from rest_framework.serializers import (
    Serializer, CharField, ListField, BooleanField, IntegerField, URLField, ChoiceField, DateTimeField,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.openapi import Parameter, IN_QUERY, TYPE_STRING

from common.documentations import Image, get_response
from common.serializers import SettingGroupSerializer
from .serializers import (
    SubCategorySerializer, MainCategorySerializer, ColorSerializer,ProductAdditionalInformationSerializer,
    TagSerializer, ProductImageSerializer, ProductMaterialSerializer, OptionSerializer, 
    ProductColorSerializer, ProductReadSerializer, ProductWriteSerializer, ProductQuestionAnswerSerializer,
    ProductQuestionAnswerClassificationSerializer, ProductRegistrationSerializer
)
from .views import (
    ProductViewSet, ProductQuestionAnswerViewSet,
    get_all_categories, get_main_categories, get_sub_categories_by_main_category, get_colors, get_tag_search_result, 
    upload_product_image, get_related_search_words, get_product_registration_data, get_product_question_answer_classification,
)


class RegistryDynamicQuerySerializer(Serializer):
    sub_category = IntegerField()


class SearchQuerySerializer(Serializer):
    search_word = CharField(min_length=1, help_text='검색어, 1글자 이상')


class ProductListQuerySerializer(Serializer):
    like = CharField()
    id = IntegerField(required=False, help_text='상품 id 필터링 - 여러 개 가능, 30개 이하\n상품 리스트는 넘긴 id 순서대로 정렬됨')
    search_word = CharField(min_length=1, required=False, help_text='검색어')
    main_category = IntegerField(required=False, help_text='메인 카테고리 필터링 - id 값')
    sub_category = IntegerField(required=False, help_text='서브 카테고리 필터링 - id 값')
    min_price = IntegerField(required=False, help_text='최소 가격 필터링')
    max_price = IntegerField(required=False, help_text='최대 가격 필터링')
    color = IntegerField(required=False, help_text='색상 필터링 - id 값, 여러 개 가능')
    coupon = IntegerField(required=False, help_text='쿠폰 필터링: 해당 쿠폰에 적용 가능한 상품 조회 - id 값')
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


class ProductRegistrationDataSerializer(ProductRegistrationSerializer):
    class MainCategoryForProductRegistration(MainCategorySerializer):
        class Meta(MainCategorySerializer.Meta):
            fields = None
            exclude = ['id', 'image_url']

    class ProductAdditionalInformationRegistrationSerializer(ProductAdditionalInformationSerializer):
        thickness = SettingGroupSerializer()
        see_through = SettingGroupSerializer()
        flexibility = SettingGroupSerializer()
        lining = SettingGroupSerializer()

        class Meta(ProductAdditionalInformationSerializer.Meta):
            ref_name = None    

    main_categories = MainCategoryForProductRegistration(many=True)
    sizes = SettingGroupSerializer(many=True)
    additional_information = ProductAdditionalInformationRegistrationSerializer()
    laundry_information = SettingGroupSerializer()
    style = SettingGroupSerializer()
    target_age_group = SettingGroupSerializer()


class ProductListResponse(Serializer):
    class ProductResultsResponse(Serializer):
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
    results = ProductResultsResponse(many=True)
    max_price = IntegerField()


class ProductDetailResponse(ProductReadSerializer):
    main_category = MainCategoryResponse()
    shopper_like = BooleanField()


class ProductQuestionAnswerResponse(Serializer):
    class ProductQuestionAnswerResultResponse(ProductQuestionAnswerSerializer):
        classification = CharField()

    count = IntegerField()
    next = URLField(allow_null=True)
    previous = URLField(allow_null=True)
    results = ProductQuestionAnswerResultResponse(many=True)


class DecoratedProductViewSet(ProductViewSet):
    shopper_token_discription = '\nShopper app의 경우 토큰이 필수 값 아님(anonymous user 가능)'
    list_description = '''상품 정보 리스트 조회
    \npage를 직접 query parameter로 전달해 원하는 페이지의 데이터를 가져올 수 있음
    \n여러 필터를 동시에 적용 가능
    * 메인 카테고리와 서브 카테고리는 동시에 필터링 할 수 없으며 여러개의 키 값을 전달할 수 없음 *
    \n'like' parameter는 value 없이 key만. token의 shopper가 좋아요 누른 상품들을 필터링
    최근 본 상품 구현을 위하여 상품 id로 필터링 지원하며 필터링할 id의 개수는 30을 넘을 수 없음
    \n기본적으로 최근 상품 등록 시간 순으로 정렬되어 있음
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

    @swagger_auto_schema(manual_parameters=[Parameter('like', IN_QUERY, type=TYPE_STRING, description='좋아요')], query_serializer=ProductListQuerySerializer,
                        **get_response(ProductListResponse()), operation_description=list_description + shopper_token_discription)
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

decorated_get_sub_categories_by_main_category_view = swagger_auto_schema(
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

decorated_get_product_registration_data_view = swagger_auto_schema(
    method='GET', **get_response(ProductRegistrationDataSerializer()), operation_description='상품 등록 시 필요한 데이터 목록'
)(get_product_registration_data)

decorated_get_product_question_answer_classification = swagger_auto_schema(
    method='GET', **get_response(ProductQuestionAnswerClassificationSerializer(many=True)), security=[], operation_description='상품 Q&A 분류 리스트 조회'
)(get_product_question_answer_classification)
