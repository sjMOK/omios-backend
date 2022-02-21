from rest_framework.serializers import *
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from common import documentation
from .serializers import MainCategorySerializer, SubCategorySerializer, ColorSerializer
from .views import get_main_categories, get_sub_categories_by_main_category, get_colors


class MainCategory(MainCategorySerializer):
    pass


class SubCategory(SubCategorySerializer):
    pass


class SubCategoryResponse(Serializer):
    main_category_id = IntegerField()
    sub_category = SubCategory(many=True)


class Color(ColorSerializer):
    pass


decorated_main_category_view = swagger_auto_schema(
    method='GET', **documentation.get_response(MainCategorySerializer(many=True)), security=[], operation_description='상품 메인 카테고리 가져오기'
)(get_main_categories)

decorated_sub_category_view = swagger_auto_schema(
    method='GET', **documentation.get_response(SubCategoryResponse()), security=[], operation_description='상품 서브 카테고리 가져오기'
)(get_sub_categories_by_main_category)

decorated_color_view = swagger_auto_schema(
    method='GET', **documentation.get_response(Color(many=True)), security=[], operation_description='상품 색상 가져오기'
)(get_colors)
