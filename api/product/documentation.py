from django.db import transaction

from rest_framework.decorators import action
from rest_framework.serializers import Serializer, CharField, ListField, BooleanField, IntegerField, URLField
from drf_yasg.utils import swagger_auto_schema

from common.documentation import Image, get_response
from .serializers import (
    SubCategorySerializer, MainCategorySerializer, SizeSerializer, LaundryInformationSerializer, ThicknessSerializer,
    SeeThroughSerializer, FlexibilitySerializer, AgeSerializer, ThemeSerializer, ColorSerializer, StyleSerializer,
    MaterialSerializer, TagSerializer, ProductImagesSerializer, ProductMaterialSerializer, OptionSerializer, 
    ProductColorSerializer, ProductReadSerializer, ProductWriteSerializer,
)
from .views import (
    ProductViewSet,
    get_all_categories, get_main_categories, get_sub_categories_by_main_category, get_colors, get_tag_search_result, 
    upload_product_image, get_related_search_word, get_common_registration_data, get_dynamic_registration_data,
)


get_dynamic_registration_data_operation_description = '''상품 등록시 필요한 동적 데이터 가져오기
parameter로 넘긴 서브 카테고리에 따라 response의 데이터(배열 길이)가 달라짐
thickness, see_through, flexibility, lining, laundry_information 빈 리스트인 경우 존재'''


class SearchQuerySerializer(Serializer):
    query = CharField()


class RegistryDynamicQuerySerializer(Serializer):
    sub_category = IntegerField()


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


class ProductCreateRequest(ProductWriteSerializer):
    class ProductMaterialCreateRequest(ProductMaterialSerializer):
        id = None  


    class ProductImageCreateRequest(ProductImagesSerializer):
        id = None


    class OptionCreateRequest(OptionSerializer):
        id = None


    class ProductColorCreateRequest(ProductColorSerializer):
        id = None


    options = OptionCreateRequest()
    images = ProductImageCreateRequest()
    materials = ProductMaterialCreateRequest()
    colors = ProductColorCreateRequest()


class ProductListResponse(Serializer):
    count = IntegerField()
    next = URLField(allow_null=True)
    previous = URLField(allow_null=True)
    results = ProductReadSerializer(many=True, allow_fields=('id', 'name', 'price', 'created'))
    max_price = IntegerField()


class ProductDetailResponse(ProductReadSerializer):
    main_category = MainCategoryResponse()


class DecoratedProductViewSet(ProductViewSet):
    shopper_token_discription = '\nShopper app의 경우 토큰이 필수 값 아님(anonymous user 가능)'
    list_description = '''상품 정보 리스트 조회
    response의 "next"는 다음 페이지의 링크, "previous"는 이전 페이지의 링크
    "next"가 null일 경우 마지막 페이지, "previous"가 null일 경우 첫 페이지 의미
    page를 직접 query parameter로 전달해 원하는 페이지의 리스트를 가져올 수 있음
    max_price는 리스트 전체 상품 가격의 최대값(한 페이지 아님에 주의)
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

    @swagger_auto_schema(**get_response(ProductListResponse()), operation_description=list_description + shopper_token_discription)
    def list(self, request):
        return super().list(request)

    @swagger_auto_schema(**get_response(ProductDetailResponse()), operation_description='상품 Id로 상품 정보 조회\n'+ shopper_token_discription)
    def retrieve(self, request, id=None):
        return super().retrieve(request, id)

    @swagger_auto_schema(request_body=ProductCreateRequest, **get_response(code=201), operation_description='상품 등록')
    @transaction.atomic
    def create(self, request):
        return super().create(request)

    @swagger_auto_schema(request_body=ProductWriteSerializer(), **get_response(), operation_description=partial_update_description)
    @transaction.atomic
    def partial_update(self, request, id=None):
        return super().partial_update(request, id)

    @swagger_auto_schema(**get_response(), operation_description='상품 Id로 상품 삭제')
    @transaction.atomic
    def destroy(self, request, id=None):
        return super().destroy(request, id)


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

decorated_get_common_registration_data_view = swagger_auto_schema(
    method='GET', **get_response(RegistryCommonResponse()), security=[], operation_description='상품 등록 시 필요한 공통(정적) 데이터 가져오기'
)(get_common_registration_data)

decorated_get_dynamic_registration_data_view = swagger_auto_schema(
    method='GET', query_serializer=RegistryDynamicQuerySerializer, **get_response(RegistryDynamicResponse()), security=[], operation_description=get_dynamic_registration_data_operation_description
)(get_dynamic_registration_data)
